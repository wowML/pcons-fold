#!/usr/bin/env python
from localconfig import *
from datetime import datetime
import sys, subprocess, os
import string as s

plot_flag = False
try:
    from plotting.plot_contact_map import plot_map
    plot_flag = True
except:
    sys.stderr.write('\nWARNING:\nBiopython not available, skip contact map plotting.\n')
    pass


def check_output(command):
    return subprocess.Popen(command, stdout=subprocess.PIPE).communicate()[0]


def main(hhblitsdb, jackhmmerdb, seqfile, n_cores=1):
    
    rundir = seqfile.rfind('/')
    if rundir < 0:
        rundir = '.'
    else:
        rundir = seqfile[:rundir]

    if hhblitsdb.endswith('_a3m_db'):
        hhblitsdb = hhblitsdb[:-7]
    if not os.path.exists(hhblitsdb + '_a3m_db'):
        sys.stderr.write('\n' + hhblitsdb + '_a3m_db' + 'does not exist\n')
        sys.exit(1)
    if not os.path.exists(jackhmmerdb):
        sys.stderr.write('\n' + jackhmmerdb + 'does not exist\n')
        sys.exit(1)
    if not os.path.exists(seqfile):
        sys.stderr.write('\n' + seqfile + 'does not exist\n')
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
        
        exists_jh = os.path.exists(seqfile + '.jh' + names[i] + '.a3m')
        exists_jh_psicov = os.path.exists(seqfile + '.jh' + names[i] + '.psicov')
        exists_jh_plmdca = os.path.exists(seqfile + '.jh' + names[i] + '.plmdca')
        exists_hh = os.path.exists(seqfile + '.hh' + names[i] + '.a3m')
        exists_hh_psicov = os.path.exists(seqfile + '.hh' + names[i] + '.psicov')
        exists_hh_plmdca = os.path.exists(seqfile + '.hh' + names[i] + '.plmdca')

        # only create alignment file if at least one of the contact maps is missing
        if not exists_jh and (not exists_jh_psicov or not exists_jh_plmdca):
            sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
            t = check_output([jackhmmer, '--cpu', str(n_cores), '-N', '5', '-E', cutoffs[i], '-A', seqfile +'.jh' + names[i] + '.ali', seqfile + '.fasta', jackhmmerdb])
            check_output([reformat, 'sto', 'a3m', seqfile + '.jh' + names[i] + '.ali', seqfile + '.jh' + names[i] + '.a3m'])
            check_output(['rm', seqfile + '.jh' + names[i] + '.ali'])

        if not exists_jh_psicov:
            #t = check_output([trim, seqfile + '.jh' + names[i] + '.fas'])
            t = check_output([trim2jones, seqfile + '.jh' + names[i] + '.a3m'])
            f = open(seqfile + '.jh' + names[i] + '.jones', 'w')
            f.write(t)
            f.close()

            t = ''
            sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
            try:
                # Joel @ NSC: Added -o flag, in case the psicov binary has not
                # been compiled with MINEFSEQS=0.
                t = check_output([psicov, '-o', seqfile + '.jh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.jh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

        jhpredictionnames.append(seqfile + '.jh' + names[i] + '.psicov')
        
        if not exists_jh_plmdca:
            t = check_output([trim2trimmed, seqfile + '.jh' + names[i] + '.a3m'])
            f = open(seqfile + '.jh' + names[i] + '.trimmed', 'w')
            f.write(t)
            f.close()

            sys.stderr.write(str(datetime.now()) + ' jackhmmer ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
            if plmdca:
                #t = check_output([plmdca, matlabdir, seqfile + '.jh' + names[i] + ".trimmed", seqfile + '.jh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(n_cores)])
                t = check_output([plmdca, seqfile + '.jh' + names[i] + ".trimmed", seqfile + '.jh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(n_cores)])
            else:
                t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + plmdcapath + "'); path(path, '" + plmdcapath + "/functions'); path(path, '" + plmdcapath + "/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.jh' + names[i] + ".trimmed', '" + seqfile + '.jh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, " + str(n_cores) + "); exit"])

        jhpredictionnames.append(seqfile + '.jh' + names[i] + '.plmdca')

        # only create alignment file if at least one of the contact maps is missing
        if not exists_hh and (not exists_hh_psicov or not exists_hh_plmdca):
            sys.stderr.write(str(datetime.now()) + ' HHblits' + names[i] + ': generating alignment\nThis may take quite a few minutes!\n ')
            t = check_output([hhblits, '-all', '-oa3m', seqfile + '.hh' + names[i] + '.a3m', '-e', cutoffs[i], '-cpu', str(n_cores), '-i', seqfile + '.fasta', '-d', hhblitsdb])
            #check_output([reformat, 'a3m', 'fas', seqfile + '.hh' + names[i] + '.a3m', seqfile + '.hh' + names[i] + '.fas'])
        
        if not exists_hh_psicov:
            #t = check_output([trim, seqfile + '.hh' + names[i] + '.fas'])
            t = check_output([trim2jones, seqfile + '.hh' + names[i] + '.a3m'])
            f = open(seqfile + '.hh' + names[i] + '.jones', 'w')
            f.write(t)
            f.close()
            
            sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running PSICOV\nThis may take more than an hour.\n')
            t = ''
            try:
                # Joel @ NSC: Added -o flag, in case the psicov binary has not
                # been compiled with MINEFSEQS=0.
                t = check_output([psicov, '-o', seqfile + '.hh' + names[i] + '.jones'])
            except:
                t = ''
            f = open(seqfile + '.hh' + names[i] + '.psicov', 'w')
            f.write(t)
            f.close()

        hhpredictionnames.append(seqfile + '.hh' + names[i] + '.psicov')
        
        if not exists_hh_plmdca:
            #t = check_output([trim2, seqfile + '.hh' + names[i] + '.fas'])
            t = check_output([trim2trimmed, seqfile + '.hh' + names[i] + '.a3m'])
            f = open(seqfile + '.hh' + names[i] + '.trimmed', 'w')
            f.write(t)
            f.close()

            sys.stderr.write(str(datetime.now()) + ' HHblits ' + names[i] + ': running plmDCA\nThis may take more than an hour.\n')
            if plmdca:
                #t = check_output([plmdca, matlabdir, seqfile + '.hh' + names[i] + ".trimmed", seqfile + '.hh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(n_cores)])
                t = check_output([plmdca, seqfile + '.hh' + names[i] + ".trimmed", seqfile + '.hh' + names[i] + ".plmdca", "0.01", "0.01", "0.1", str(n_cores)])
            else:
                t = check_output([matlab, '-nodesktop', '-nosplash', '-r', "path(path, '" + plmdcapath + "'); path(path, '" + plmdcapath + "/functions'); path(path, '" + plmdcapath + "/3rd_party_code/minFunc/'); plmDCA_symmetric ( '" + seqfile + '.hh' + names[i] + ".trimmed', '" + seqfile + '.hh' + names[i] + ".plmdca', 0.01, 0.01, 0.1, " + str(n_cores) + "); exit"])
        hhpredictionnames.append(seqfile + '.hh' + names[i] + '.plmdca')

    sys.stderr.write("Predicting...\n")
    #l = [os.path.dirname(os.path.abspath(sys.argv[0])) + '/predict.py']
    l = [root + '/predict.py']
    l.extend(jhpredictionnames)
    l.extend(hhpredictionnames)
    results = check_output(l)

    f = open(seqfile + '.pconsc.out', 'w')
    f.write(results)
    f.close()


    # plot the top L*1 contacts in a contact map
    # those contacts are later used during protein folding
    if plot_flag:
        if os.path.exists('native.pdb') and os.path.exists(seqfile + '.horiz'):
            plot_map(seqfile, seqfile + '.pconsc.out', 1.0, pdb_filename='native.pdb', psipred_filename=seqfile + '.horiz')
        elif os.path.exists('native.pdb'):
            plot_map(seqfile, seqfile + '.pconsc.out', 1.0, pdb_filename='native.pdb')
        elif os.path.exists(seqfile + '.horiz'):
            plot_map(seqfile, seqfile + '.pconsc.out', 1.0, psipred_filename=seqfile + '.horiz')
        else:
            plot_map(seqfile, seqfile + '.pconsc.out', 1.0)


if __name__ == "__main__":

    ### parse parameters

    if len(sys.argv) < 4:
        print sys.argv[0], '[-c n_cores] <hhblits db> <jackhmmer db> <sequence file>'
        sys.exit(0)

    if '-c' in sys.argv:
        idx = sys.argv.index('-c')
        try:
            n_cores = int(sys.argv[idx+1])
        except:
            print 'Number of cores -c must be an integer, %r is not. Default is %s.' % (sys.argv[idx+1], n_cores)
            sys.exit(1)
        del sys.argv[idx +1]
        del sys.argv[idx]

    hhblitsdb = sys.argv[1]
    jackhmmerdb = sys.argv[2]
    seqfile = sys.argv[3]

    main(hhblitsdb, jackhmmerdb, seqfile, n_cores=n_cores)
