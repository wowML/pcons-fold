#!/usr/bin/env python

from localconfig import *
from datetime import datetime
import sys, subprocess, os
import string as s

def check_output(command):
    return subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]
    
if len(sys.argv) < 2:
    print sys.argv[0], '<sequence file>'
    sys.exit(0)

seqfile = sys.argv[1]

rundir = seqfile.rfind('/')
if rundir < 0:
    rundir = '.'
else:
    rundir = seqfile[:rundir]

if not os.path.exists(seqfile):
    print seqfile, 'does not exist'
    sys.exit(0)

f = open(seqfile).read()

if os.path.exists(seqfile + '.fasta'):
    subprocess.call(['mv', seqfile + '.fasta', seqfile +'.bak'])

f2 = open(seqfile +'.fasta', 'w')
if f[0] != '>':
    f2.write('>target\n' + f +'\n')
else:
    x = f.split('\n')
    if len(x[0]) > 6:
        target = x[0][1:5] + x[0][6]
    f2.write('>target\n' + "".join(x[1:]) + '\n')
f2.close()

names = ['E4', 'E0', 'E10', 'E40']
cutoffs = ['1e-4', '1', '1e-10', '1e-40']

jhpredictionnames = []
hhpredictionnames = []
failed = []

for i in range(4):
    if not os.path.exists(seqfile + '.jh' + names[i] + '.fas'):
        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
        t = check_output([jackhmmer, '--cpu', str(cores), '-N', '5', '-E', cutoffs[i], '-A', seqfile +'.jh' + names[i] + '.ali', seqfile + '.fasta', jackhmmerdb])
        check_output([reformat, 'sto', 'fas', seqfile + '.jh' + names[i] + '.ali', seqfile + '.jh' + names[i] + '.fas'])
        check_output(['rm', seqfile + '.jh' + names[i] + '.ali'])

    if not os.path.exists(seqfile + '.jh' + names[i] + '.psicov'):
        t = check_output([trim, seqfile + '.jh' + names[i] + '.fas'])
        f = open(seqfile + '.jh' + names[i] + '.jones', 'w')
        f.write(t)
        f.close()

        t = ''
        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
        if not os.path.exists(seqfile + '.jh' + names[i] + '.psicov'):
            try:
                t = check_output([psicov, seqfile + '.jh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.jh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

           jhpredictionnames.append(seqfile + '.jh' + names[i] + '.psicov')
    
    if not os.path.exists(seqfile + '.jh' + names[i] + '.plmdca'):
        t = check_output([trim2, seqfile + '.jh' + names[i] + '.fas'])
        f = open(seqfile + '.jh' + names[i] + '.trimmed', 'w')
        f.write(t)
        f.close()

        sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
        t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + scriptpath + "/plmDCA_symmetric_v2'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/functions'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.jh' + names[i] + ".trimmed', '" + seqfile + '.jh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, 4); exit"])

    jhpredictionnames.append(seqfile + '.jh' + names[i] + '.plmdca')

    if not os.path.exists(seqfile + '.hh' + names[i] + '.fas'):
        sys.stderr.write(str(datetime.now()) + ' HHblits' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
        t = check_output([hhblits, '-all', '-oa3m', seqfile + '.hh' + names[i] + '.a3m', '-e', cutoffs[i], '-cpu', str(cores), '-i', seqfile + '.fasta', '-d', hhblitsdb])
        check_output([reformat, 'a3m', 'fas', seqfile + '.hh' + names[i] + '.a3m', seqfile + '.hh' + names[i] + '.fas'])
    
    if not os.path.exists(seqfile + '.hh' + names[i] + '.psicov'):
        t = check_output([trim, seqfile + '.hh' + names[i] + '.fas'])
        f = open(seqfile + '.hh' + names[i] + '.jones', 'w')
        f.write(t)
        f.close()
        
        sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
        t = ''
        if not os.path.exists(seqfile + '.hh' + names[i] + '.psicov'):
            try:
                t = check_output([psicov, seqfile + '.hh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.hh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

        hhpredictionnames.append(seqfile + '.hh' + names[i] + '.psicov')
    
    if not os.path.exists(seqfile + '.hh' + names[i] + '.plmdca'):
        t = check_output([trim2, seqfile + '.hh' + names[i] + '.fas'])
        f = open(seqfile + '.hh' + names[i] + '.trimmed', 'w')
        f.write(t)
        f.close()

        sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
        t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + scriptpath + "/plmDCA_symmetric_v2'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/functions'); path(path, '" + scriptpath + "/plmDCA_symmetric_v2/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.hh' + names[i] + ".trimmed', '" + seqfile + '.hh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, 4); exit"])
    hhpredictionnames.append(seqfile + '.hh' + names[i] + '.plmdca')


if not os.path.exists(seqfile + '.rsa'):
    sys.stderr.write(str(datetime.now()) + ': running NetSurfP\nThis may take quite a few minutes!\n')
    t = check_output([netsurf, '-i', seqfile, '-a'])
    f = open(seqfile + '.rsa', 'w')
    f.write(t)
    f.close()

if not os.path.exists(seqfile + '.psipred'):
    sys.stderr.write(str(datetime.now()) + ': running Psipred\nThis may take quite a few minutes!\n')
    check_output([psipred, seqfile])

sys.stderr.write("Predicting layer 0...\n")
result_i_name = seqfile + '.layer0.out'
l = [os.path.dirname(os.path.abspath(sys.argv[0])) + '/predict-l0.py']
l.extend(jhpredictionnames)
l.extend(hhpredictionnames)
l.extend([nfpredictionname, sspredictionname, result_i_name])
check_output(l)

for layer_i in xrange(1, layers + 1)
    sys.stderr.write("Predicting layer %s...\n" % layer_i)
    prev_result_i_name = result_i_name
    result_i_name = seqfile + '.layer' + layer_i + '.out'
    l = [os.path.dirname(os.path.abspath(sys.argv[0])) + '/predict-ln.py']
    l.append(layer_i)
    l.extend(jhpredictionnames)
    l.extend(hhpredictionnames)
    l.extend([netsurfpredictionname, sspredictionname, lipredictionname, prev_result_i_name, result_i_name])
    check_output(l)

