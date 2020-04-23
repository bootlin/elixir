#!/usr/bin/env python3
from time import time
import os
import sys

BOLD = '\033[1m'
NORMAL = '\033[0m'

ELIXIR_DIR = os.path.dirname(__file__) + '/..'
sys.path = [ ELIXIR_DIR ] + sys.path

#Parameters
run_number = 100
verbose = False

#List of test elements
project = 'linux'
versions = ['latest', 'v5.6.2']
idents = [  'loopback', 
            'devm_register_reboot_notifier',
            'notrace',
            'arch_local_irq_restore',
            'blk_queue_dma_alignment',
            'spinlock_t',
            'max',
            'task_struct',
            'eth_header',
            'sk_buff' ]

files = [   '/block/partitions/osf.c', 
            '/mm/kasan/quarantine.c', 
            '/include/crypto/internal/hash.h', 
            '/drivers/gpu/drm/gma500/gma_display.c',
            '/drivers/hwmon/pmbus/ltc2978.c',
            '/virt/lib/irqbypass.c',
            '/Makefile',
            '/fs/btrfs/tree-checker.c',
            '/kernel/locking/qspinlock_stat.h',
            '/arch/arm/boot/dts/armada-375.dtsi' ]


#Test results
idents_results = []
idents_max = 0
idents_min = 0
idents_average = 0

files_results = []
files_max = 0
files_min = 0
files_average = 0


def init_query(project):
    if 'LXR_PROJ_DIR' not in os.environ:
        print("ERROR : LXR_PROJ_DIR not defined !")
        return None;

    basedir = os.environ['LXR_PROJ_DIR']
    os.environ['LXR_DATA_DIR']= basedir + '/' + project + '/data'
    os.environ['LXR_REPO_DIR'] = basedir + '/' + project + '/repo'
    
    import query
    return query.query


def get_ident(ident, version):
    if version == 'latest':
            version = query('latest')

    return query('ident', version, ident)

def get_file(path, version):
    if version == 'latest':
            version = query('latest')

    return query('file', version, path)


#Read arguments
if(len(sys.argv) > 1):
    if(sys.argv[1] == '-v'):
        verbose = True
    elif (sys.argv[1] == '-h'):
        print("LXR_PROJ_DIR needs to be set before launching this script\n" +
                "Options :\n" +
                "-v     Verbose mode (Show requests details)")
        exit()

#Query init
query = init_query(project)
if(query == None):
    exit()

#Database test
print((BOLD + "Database test for project {}" + NORMAL).format(project))

print("Each test runs {} times".format(run_number))

for version in versions:
    print((BOLD + "\nVersion tested : {}\n" + NORMAL).format(version))

    print(BOLD + "Identifiers access test\n" + NORMAL)
    for i in range(run_number):
        for ident in idents:
            start_time = time()
            get_ident(ident, version)
            end_time = time()

            elapsed_time = (end_time - start_time)*1000 #convert to ms
            idents_results.append(elapsed_time)

            if verbose:
                print("Identifier : {}".format(ident))
                print("Elapsed time : {0:.6f} ms\n".format(elapsed_time))


    idents_min = min(idents_results)
    idents_max = max(idents_results)
    idents_average = sum(idents_results)/len(idents_results)

    print((BOLD + "Min:" + NORMAL + " {0:.6f} ms\n" 
            + BOLD + "Max:" + NORMAL + " {1:.6f} ms\n"
            + BOLD + "Average:" + NORMAL + " {2:.6f} ms\n"
            ).format(idents_min, idents_max, idents_average))

    print(BOLD + "Files access test\n" + NORMAL)
    for i in range(run_number):
        for file in files:
            start_time = time()
            get_file(file, version)
            end_time = time()

            elapsed_time = (end_time - start_time) * 1000 #convert to ms
            files_results.append(elapsed_time)

            if verbose:
                print("File : {}".format(file))
                print("Elapsed time : {0:.6f} ms\n".format(elapsed_time))


    files_min = min(files_results)
    files_max = max(files_results)
    files_average = sum(files_results)/len(files_results)

    print((BOLD + "Min:" + NORMAL + " {0:.6f} ms\n" 
            + BOLD + "Max:" + NORMAL + " {1:.6f} ms\n"
            + BOLD + "Average:" + NORMAL + " {2:.6f} ms\n"
            ).format(files_min, files_max, files_average))