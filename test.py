# PRs are welcome!
# Author's discord tag: JakubBlaha#7575

import argparse
import os
import subprocess

HEADER = '\033[95m'
OKBLUE = '\033[94m'
OKCYAN = '\033[96m'
OKGREEN = '\033[92m'
WARNING = '\033[93m'
FAIL = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'

PROJ_OUT_FILE = "proj2.out"


def error(*args):
    print(FAIL + "Error:", *args, ENDC)


def success(*args):
    print(OKGREEN + "Success:", *args, ENDC)


def log_should_start_with_one(output):
    if output[0].split(":")[0] != '1':
        error("Logs don't start with number 1!")
        return False

    success("Logs start with number 1")
    return True


def check_log_numbers_ascending(output):
    last_log_n = int(output[0].split(":")[0])

    for line in output[1:]:
        log_n = int(line.split(":")[0])

        if log_n != last_log_n + 1:
            error("Found a log lines whichs' log numbers are not in ascending order!")
            return False

        last_log_n = log_n

    success("Log line numbers are ascending.")
    return True


def all_entities_logged(output, entity, n_entity, msg_substr):
    d = {i + 1: False for i in range(n_entity)}

    for line in output:
        if msg_substr in line:
            _, line_en, msg = line.split(":")

            if line_en[1] == entity:
                entity_id = int(line_en[3:])
                d[entity_id] = True

    ok = True

    for k, v in d.items():
        if not v:
            error(f"{msg_substr} not logged by entity {entity} {k}")
            ok = False

    if ok:
        success(f"All entities {entity} logged {msg_substr}.")

    return ok


def no_duplicate_logs(output, entity, n, log_msg):
    d = {}

    for i in range(1, n + 1):
        d[f" {entity} {i}"] = 0

    for line in output:
        _, line_en, msg = line.split(":")

        if line_en[1] == entity and log_msg in msg:
            try:
                d[line_en] += 1
            except KeyError:
                error("Found unexpected line:", line.strip())

    ok = True

    for k, v in d.items():
        if v > 1:
            error(
                f"Duplicated log found for{k} when searching for logs of {log_msg}!")
            ok = False

    if ok:
        success(f"No duplicate logs of {log_msg} found for entities {entity}.")

    return ok


def closing_exactly_once(output):
    if len([i for i in output if ": closing\n" in i]) != 1:
        error("closing log not present exactly once")
        return False

    return True


def taking_break_and_break_finished_match(output, n_worker):
    d = {i + 1: 0 for i in range(n_worker)}

    for line in output:
        if "taking break" in line:
            worker_id = int(line.split(":")[1][3:])
            d[worker_id] += 1

        elif "break finished" in line:
            worker_id = int(line.split(":")[1][3:])
            d[worker_id] -= 1

    ok = True

    for k, v in d.items():
        if v != 0:
            error("Number of taking break and break finished logs for worker ID",
                  k, "do not match!")
            ok = False

    if ok:
        success("Number of taking break and break finished logs match for all workers.")

    return ok


def check_no_entering_after_close(output):
    closing_log_seen = False

    ok = True

    for line in output:
        if closing_log_seen:
            if "entering office for a service" in line:
                error("Entering office log seen after closing log")
                ok = False
        elif "closing" in line:
            closing_log_seen = True

    if ok:
        success("No entering office log after closing log")

    return ok


def no_unallowed_breaks(output):
    d = {'1': 0, '2': 0, '3': 0}

    ok = True

    for line in output:
        if "entering office for a service" in line:
            service_n = line.strip()[-1]
            d[service_n] += 1
        elif "taking break" in line:
            if d['1'] or d['2'] or d['3']:
                error("Customer not served ASAP!")
                ok = False
        elif "serving a service of type" in line:
            service_n = line.strip()[-1]
            d[service_n] -= 1

    if ok:
        success("All customers served ASAP.")

    return ok


def entering_and_serving_match(output):
    d = {'1': 0, '2': 0, '3': 0}

    for line in output:
        if "entering office for a service" in line:
            service_n = line.strip()[-1]
            d[service_n] += 1
        elif "serving a service of type" in line:
            service_n = line.strip()[-1]
            d[service_n] -= 1

    ok = True

    for k, v in d.items():
        if v > 0:
            error(f"Service line {k} left with unsat customers!")
            ok = False

        if v < 0:
            error(
                f"Service line {k} had more cusomers served than how many there were in line!?")
            ok = False

    if ok:
        success(
            "Entering office for service ... and serving a service of type ... logs match.")

    return ok


def main():
    parser = argparse.ArgumentParser(description='IOS Project 2 tester')

    parser.add_argument('executable', type=str,
                        help='Description of argument 1')
    parser.add_argument('NZ', type=int)
    parser.add_argument('NU', type=int)
    parser.add_argument('TZ', type=int)
    parser.add_argument('TU', type=int)
    parser.add_argument('F', type=int)

    args = parser.parse_args()

    full_exec_path = os.path.realpath(args.executable)

    n_cust = args.NZ
    n_worker = args.NU
    t_cust = args.TZ
    t_worker = args.TU
    f = args.F

    proj_args = list(map(str, [n_cust, n_worker, t_cust, t_worker, f]))

    print("Using executable:", full_exec_path)
    print("Using arguments:", proj_args)

    result = subprocess.run([full_exec_path, *proj_args])

    print("Program exit code:", result.returncode)

    try:
        with open(PROJ_OUT_FILE, 'r') as f:
            output = f.readlines()
    except FileNotFoundError:
        error("Output file", PROJ_OUT_FILE, "not found!")
        return

    print("========== This is your project output ==========")
    print(*output, sep="")
    print("========== This is the end of your project output ==========")

    print("Your output contains", len(output), "lines (line breaks)")

    if (len(output) < 1):
        error("Output file empty!")
        return

    log_should_start_with_one(output)
    check_log_numbers_ascending(output)

    no_closing_out = [line for line in output if not "closing" in line]

    all_entities_logged(no_closing_out, "Z", n_cust, "started")
    all_entities_logged(no_closing_out, "U", n_worker, "started")

    all_entities_logged(no_closing_out, "Z", n_cust, "going home")
    all_entities_logged(no_closing_out, "U", n_worker, "going home")

    no_duplicate_logs(no_closing_out, 'Z', n_cust, "started")
    no_duplicate_logs(no_closing_out, 'U', n_worker, "started")

    no_duplicate_logs(no_closing_out, 'Z', n_cust, "going home")
    no_duplicate_logs(no_closing_out, 'U', n_worker, "going home")

    no_duplicate_logs(no_closing_out, 'Z', n_cust,
                      "entering office for a service")
    no_duplicate_logs(no_closing_out, 'Z', n_cust, "called by office worker")

    closing_exactly_once(output)
    taking_break_and_break_finished_match(output, n_worker)
    check_no_entering_after_close(output)
    no_unallowed_breaks(output)
    entering_and_serving_match(output)


if __name__ == "__main__":
    main()
