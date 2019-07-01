from pybatfish.client.commands import *
from pybatfish.question.question import load_questions
from pybatfish.datamodel.flow import (HeaderConstraints,
                                         PathConstraints)
from pybatfish.question import bfq
import logging
import random
import sys

def print_diff_reachability(answer):
    print("")
    for flow_n, flow in enumerate(answer['Flow']):
        print("FLOW: {}".format(flow))
        for trace_n, trace in enumerate(answer['Snapshot_Traces'][flow_n]):
            for steps in trace:
                print("{}".format(steps))
        print("")


random.seed(80)

logging.disable(sys.maxsize)

NETWORK_NAME = "ebgp-spine-leaf-network1"
BASE_SNAPSHOT_NAME = "ebgp-spine-leaf-snapshot1"
SNAPSHOT_PATH = sys.argv[1]
BATFISH_SERVICE_IP = "172.29.236.139"
MAX_CHAOS = 15

bf_session.host = BATFISH_SERVICE_IP
load_questions()

print("[*] Initializing BASE_SNAPSHOT")
bf_set_network(NETWORK_NAME)
bf_init_snapshot(SNAPSHOT_PATH, name=BASE_SNAPSHOT_NAME, overwrite=True)

print("[*] Collecting link data")
links = bfq.edges(nodes="/spine|leaf/",remoteNodes="/spine|leaf/").answer(BASE_SNAPSHOT_NAME).frame()

print("[*] Releasing the Chaos Monkey")
for i in range(MAX_CHAOS):
    failed_link1_index = random.randint(0, len(links) - 1)
    failed_link2_index = random.randint(0, len(links) - 1)
    print(" - Deactivating Links:{} + {}".format(links.loc[failed_link1_index].Interface,
                                                  links.loc[failed_link2_index].Interface))

    FAIL_SNAPSHOT_NAME = "fail_snapshot"
    bf_fork_snapshot(
        BASE_SNAPSHOT_NAME,
        FAIL_SNAPSHOT_NAME,
        deactivate_interfaces=[links.loc[failed_link1_index].Interface,
                               links.loc[failed_link2_index].Interface],
        overwrite=True
    )

    answer = bfq.differentialReachability(
        headers=HeaderConstraints(dstIps='server2')
    ).answer(
        snapshot=FAIL_SNAPSHOT_NAME,
        reference_snapshot=BASE_SNAPSHOT_NAME
    ).frame()

    if len(answer) > 0:
        print("[FAIL] difference found between BASE_SNAPSHOT and FAIL_SNAPSHOT")
        print_diff_reachability(answer)
        sys.exit(1)

print("[SUCCESS] No reachability issues found after {} rounds of chaos!".format(MAX_CHAOS))