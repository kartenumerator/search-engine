from multiprocessing import Process, Queue
from collections import deque
from rich.live import Live
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import time

def main(log_queue: Queue, CONCURRENT_REQUESTS: int):
    header = "Starting..."
    logs = {
        "a": deque(maxlen=50),
        "b": deque(maxlen=CONCURRENT_REQUESTS),
        "c": deque(maxlen=50),
    }

    # -----------------------
    # Layout
    # -----------------------
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="body"),
    )
    layout["body"].split_row(
        Layout(name="log_a"),
        Layout(name="log_b"),
        Layout(name="log_c"),
    )

    for i in range(CONCURRENT_REQUESTS):
        logs["b"].append(f"{i+1} : ")

    # -----------------------
    # Render helpers
    # -----------------------
    def render_header():
        return Panel(header, title="STATUS")

    def render_log(title, data, color):
        table = Table.grid()
        for line in data:
            table.add_row(f"{line}")
        return Panel(table, title=title, border_style=color)

    # -----------------------
    # Start worker
    # -----------------------
    # log_queue = Queue()
    # p = Process(target=worker, args=(log_queue,), daemon=True)
    # p.start()

    # -----------------------
    # Live UI loop
    # -----------------------
    with Live(layout, refresh_per_second=10, screen=True):
        while True:
            # Drain queue (NON-BLOCKING)
            while not log_queue.empty():
                key, message = log_queue.get()
                if key == "header":
                    header = message
                elif isinstance(key, int):
                    logs["b"][key] = f"{key+1} : {message}"
                else:
                    logs[key].append(message)

            # header = f"Total logs: {sum(len(v) for v in logs.values())}"

            layout["header"].update(render_header())
            layout["log_a"].update(render_log("MAIN", reversed(logs["a"]), "green"))
            layout["log_b"].update(render_log("WORKERS", logs["b"], "yellow"))
            layout["log_c"].update(render_log("DATABASE", reversed(logs["c"]), "magenta"))

            time.sleep(0.1)
