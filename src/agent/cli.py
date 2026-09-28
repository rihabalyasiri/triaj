# cli.py
import argparse
import json
import os
import warnings
from itertools import islice

# --- Silence library noise. Must run BEFORE transformers ---
os.environ.setdefault("HF_HUB_VERBOSITY", "error")          # "unauthenticated requests" warning
os.environ.setdefault("HF_HUB_DISABLE_PROGRESS_BARS", "1")  # download bars
os.environ.setdefault("TRANSFORMERS_VERBOSITY", "error")
warnings.filterwarnings("ignore", category=FutureWarning)   # torch.jit warning on Python 3.14

from transformers.utils import logging as hf_logging  
hf_logging.set_verbosity_error()
hf_logging.disable_progress_bar()                    

from rich import box                                   
from rich.console import Console, Group                
from rich.panel import Panel                          
from rich.table import Table                           
from rich.text import Text                             

import agent.enricher             
import agent.adapter                   
import agent.writer      
import agent.triage
import agent.action                 
import agent.checker 

console = Console()

PRIORITY_STYLE = {"high": "bold red", "medium": "yellow", "low": "green"}
ESCALATE_ACTION = "escalate to human supervisor"
ASK_CUSTOMER_ACTION = "ask customer for more information"


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

def triage_record(i: int, message: str, use_llm: bool = True) -> dict:
    """Topic -> priority -> action -> LLM check for one ticket, merged into one row."""
    row = {"id": i, "message": message}
    try:
        topic = agent.triage.classify_ticket(message)         
        row.update(topic)

        priority = agent.triage.predict_priority(message, topic["predicted_topic"])
        row.update(priority)                     

        action = agent.action.decide_action(topic["predicted_topic"], priority["predicted_priority"], row["urgency"])
        row.update(action)                        
    except Exception as e:
        row["error"] = str(e)
        row["status"] = "error"
        return row

    if use_llm:
        try:
            check = agent.checker.check_ticket(message, topic["predicted_topic"],
                                 priority["predicted_priority"], action["escalated"])
        except Exception as e:
            # Keep the NLI result; mark the row so you can re-run the check later.
            row["error"] = f"LLM check failed: {e}"
            row["status"] = "partial"
            return row

        row.update(agent.checker.check_to_row(check))

        # Final decision: escalate if the rules,
        # otherwise ask the customer when the ticket is ambiguous.
        if check.ambiguous and not row["escalated"]:
            row["action"] = ASK_CUSTOMER_ACTION

    row["status"] = "ok"
    return row


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def shorten(text, width: int = 220) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= width else text[:width].rstrip() + " …"


def render_ticket(row: dict, full: bool = False) -> None:
    message = str(row["message"]) if full else shorten(row["message"])

    if row.get("status") == "error":
        body = Group(Text(row.get("error", ""), style="bold red"), Text(""),
                     Text(message, style="italic dim"))
        console.print(Panel(body, title=f"Ticket #{row['id']} · error",
                            title_align="left", border_style="red", box=box.ROUNDED))
        return

    prio = row["predicted_priority"]
    style = "bold red" if row.get("escalated") else PRIORITY_STYLE.get(prio, "white")

    details = Table.grid(padding=(0, 2))
    details.add_column(style="dim", justify="right")
    details.add_column()
    details.add_row("Topic", Text.assemble(
        (row["predicted_topic"], "bold"), (f"  confidence {row['confidence']:.2f}", "dim")))
    details.add_row("Priority", Text.assemble(
        (prio.upper(), PRIORITY_STYLE.get(prio, "white")),
        (f"  score {row['priority_score']:.2f} · urgency {row['urgency']:.2f}", "dim")))

    if "llm_topic" in row:
        details.add_row("LLM review", Text.assemble(
            ("topic ", "dim"), (row["llm_topic"], "bold"),
            ("  priority ", "dim"), (row["llm_priority"].upper(), PRIORITY_STYLE.get(row["llm_priority"], "white"))))
        details.add_row("Ambiguous", Text.assemble(
            ("yes", "bold yellow") if row["ambiguous"] else ("no", ""),
            (f"  {row['ambiguity_reason']}", "dim") if row["ambiguous"] else ("", "")))

    details.add_row("Action", Text(row["action"], style="bold"))
    escalated_text = Text("yes", style="bold red") if row["escalated"] else Text("no")
    if row["escalated"] and row.get("escalation_reason"):
        escalated_text.append(f"  {row['escalation_reason']}", style="dim")
    details.add_row("Escalated", escalated_text)

    parts = [Text(message, style="italic"), Text(""), details]

    if row.get("ambiguous") and row.get("customer_reply"):
        questions = Text("\n".join(f"• {q}" for q in row["follow_up_questions"].split(" | ") if q))
        parts += [Text(""), Text("Follow-up questions", style="bold yellow"), questions,
                  Text(""), Text("Suggested reply to customer", style="bold yellow"),
                  Text(row["customer_reply"])]

    if row.get("status") == "partial":
        parts += [Text(""), Text(row.get("error", ""), style="red")]

    console.print(Panel(Group(*parts), title=f"Ticket #{row['id']}", title_align="left",
                        border_style=style, box=box.ROUNDED))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def cli_app():
    p = argparse.ArgumentParser(prog="triage", description="Triage tickets from the preprocessor")
    p.add_argument("-n", "--num", type=int, default=None,
                   help="number of records to process (default: all)")
    p.add_argument("--json", action="store_true",
                   help="print each result as indented, colored JSON instead of panels")
    p.add_argument("--full", action="store_true",
                   help="show the full ticket message instead of a shortened preview")
    p.add_argument("--no-llm", action="store_true",
                   help="skip the LLM check (NLI + rules only, much faster)")
    args = p.parse_args()
    if args.num is not None and args.num < 1:
        p.error("-n must be >= 1")
    use_llm = not args.no_llm

    with console.status("Loading tickets…"):
        df = agent.adapter.read_file("tickets.csv")
    records = islice(agent.enricher.preprocessing(df), args.num)

    total = errors = escalated = ambiguous = 0
    with agent.writer.open_results() as writer:
        for i, rec in enumerate(records, start=1):
            label = f" + {agent.checker.OLLAMA_MODEL} check" if use_llm else ""
            with console.status(f"Triaging ticket #{i}{label}…"):
                row = triage_record(i, rec.get("message"), use_llm=use_llm)
                # Ground truth for evaluation only: attached after triage, never seen by the models.
                row["queue"] = rec["queue"]
                row["priority"] = rec["priority"]

            if args.json:
                row_out = row if args.full else {**row, "message": shorten(row["message"])}
                console.print_json(json.dumps(row_out, ensure_ascii=False))
            else:
                render_ticket(row, full=args.full)

            writer.writerow(row)  # CSV always gets the full message
            total += 1
            errors += row["status"] in ("error", "partial")
            escalated += bool(row.get("escalated"))
            ambiguous += bool(row.get("ambiguous"))

    console.print(
        f"\n[bold]Processed {total} tickets[/bold] · "
        f"[red]{escalated} escalated[/red] · "
        f"[yellow]{ambiguous} ambiguous[/yellow] · "
        f"{'[red]' if errors else '[green]'}{errors} errors[/]\n"
        f"[dim]Results written to {agent.writer.OUT_PATH.resolve()}[/dim]"
    )
