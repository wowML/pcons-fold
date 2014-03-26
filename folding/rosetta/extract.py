import sys
import os
from subprocess import call

import evaluate_scores as ev

from localconfig import *

### default value = relax top-ranked structures
relax_flag = True

### parse parameters
if '-c' in sys.argv:
    idx = sys.argv.index('-c')
    try:
        n_cores = int(sys.argv[idx+1])
    except:
        print 'Number of cores -c must be an integer, %r is not. Default is %s.' % (sys.argv[idx+1], n_cores)
        sys.exit(1)
    del sys.argv[idx+1]
    del sys.argv[idx]

if '--norelax' in sys.argv:
    idx = sys.argv.index('--norelax')
    relax_flag = False
    del sys.argv[idx]

seqfile = os.path.abspath(sys.argv[1])
num = int(sys.argv[2])

rundir = os.path.dirname(os.path.abspath(seqfile)) + '/'

### determine IDs of top scoring decoys
all_scores_sorted = ev.get_best_of_all_runs(num, n_cores, rundir + 'rosetta')

### extract given IDs
ev.extract_structures(all_scores_sorted)

### and relax the models if given (RECOMMENDED)
if relax_flag:
    ev.relax_structures(all_scores_sorted)

### calculate similarity scores to native structure, if given
### and store them in "TMscores.txt"
if os.path.exists(rundir + 'native.pdb'):
    scorestr = ev.compare_to_native(all_scores_sorted, relax_flag, False)
    scorefile = open(rundir + 'rosetta/TMscores.txt', 'w')
    scorefile.write(scorestr)
    scorefile.close()
 
### collect the results in seperate folder
call(['mkdir', rundir + 'rosetta_results'])
call('mv %s/rosetta/*.run_*.*.pdb %s/rosetta_results' % (rundir, rundir), shell=True)

if os.path.exists(rundir + 'native.pdb'):
    call(['mv', rundir + 'rosetta/TMscores.txt', rundir + 'rosetta_results'])

