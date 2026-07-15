import multiprocessing as mp
import time


def manage_process_pool(processes: list[mp.Process], max_simultaneous: int):
    run_parallel(processes, max_simultaneous)


def run_parallel(
    processes: list[mp.Process],
    max_simultaneous: int,
) -> None:
    """
    Takes a list of instantiated Process objects and runs them
    with a maximum concurrency of max_simultaneous.
    """
    pending: list[mp.Process] = processes.copy()  # Processes waiting to start
    running: list[mp.Process] = []  # Processes currently executing

    N = len(pending)
    DT_SHORT = 0.1
    DT_LONG = 1.0
    n_done = 0
    n_ok = 0
    n_fail = 0
    print(f"Total jobs to execute: {N}. Max simultaneous: {max_simultaneous}\n")

    # Keep looping as long as we have jobs waiting to start OR jobs currently running
    while pending or running:
        # 1. Check for completed processes and remove them from the running list
        # We iterate over a copy of the list [:] so we can safely remove items inside the loop
        active = False
        for p in running[:]:
            if not p.is_alive():
                active = True

                p.join()  # Clean up the process completely
                running.remove(p)
                n_done += 1

                if p.exitcode == 0:
                    strStatus = "ok"
                    n_ok += 1
                else:
                    strStatus = "with error"
                    n_fail += 1

                print(
                    f"\nJob {p.name} finished {strStatus}"
                    + f" pending/running/done = {len(pending)}/{len(running)}/{n_done}"
                    + f" oks/fails = {n_ok}/{n_fail}",
                    flush=True,
                )

        # 2. Fill up empty slots if we are below max_simultaneous
        while len(running) < max_simultaneous and pending:
            active = True

            next_process = pending.pop(0)
            next_process.start()
            running.append(next_process)
            print(
                f"Job {next_process.name} started."
                + f" pending/running/done = {len(pending)}/{len(running)}/{n_done}",
                flush=True,
            )

        # 3. Sleep briefly to prevent this monitoring loop from maxing out the CPU
        if running:
            if active:
                time.sleep(DT_SHORT)
            else:
                time.sleep(DT_LONG)

    print(f"\nAll processes have completed, oks/fails={n_ok}/{n_fail}")
    if n_fail:
        fails = [p for p in processes if p.exitcode != 0]
        print(
            f"fail id: {' '.join([f.name.split('-')[-1] if f.name.startswith('Process-') else f.name for f in fails])}"
        )


def run_sequential(processes: list[mp.Process]) -> None:
    for p in processes:
        p.start()
        p.join()
