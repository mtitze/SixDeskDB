#!/usr/bin/env python

# python executable for SixdeskDB
# Moonis Javed <monis.javed@gmail.com>,
# Riccardo De Maria <riccardo.de.maria@cern.ch>
# Xavier Valls Pla  <xavier.valls.pla@cern.ch>
# Danilo Banfi <danilo.banfi@cern.ch>
#
# From 2019 in Python3 onwards:
# Malte Titze <malte.titze@cern.ch>
#
# This software is distributed under the terms of the GNU Lesser General Public
# License version 2.1, copied verbatim in the file ``COPYING''.

# In applying this licence, CERN does not waive the privileges and immunities
# granted to it by virtue of its status as an Intergovernmental Organization or
# submit itself to any jurisdiction.

import sys, os, time

if sys.version_info < (3, 6):
  print("SixDeskDB tested with Python version >= 3.6")
  print("Remove this check at your own risk.")
  sys.exit(1)

from sixdeskdb import SixDeskDB, Mad6tOut, RunDaVsTurns, RunDaVsTurnsAng, PlotDaVsTurns, PlotCompDaVsTurns, PlotFMA, PlotGrid
#from dbtocentral,config

def str2bool(st):
  if(st=='True' or st=='true'):
    return True
  else:
    return False


def guess_toolkit():
  try:
    import PyQt4
    return 'qt'
  except ImportError:
    return 'tk'

class SixDB(object):
    def __init__(self,argsv):
        self.args=argsv[1:]
        self.verbose=True
    def run(self):
        args=self.args
        if len(args)==0:
            self.help()
        elif len(args)==1:
            cmd=self.args[0]
            self.help(cmd)
        else:
            study=self.args[0]
            cmd=self.args[1]
            if not hasattr(self,cmd):
                print("Error: command `%s' not found"%cmd)
                print(self.help(cmd))
            else:
              try:
                getattr(self,cmd)(study)
              except Exception as e:
                print()
                print("Error in `%s' command."%cmd)
                import traceback
                print()
                exc_type, exc_value, exc_tb = sys.exc_info()
                traceback.print_exception(exc_type, exc_value, exc_tb)
                #print "%s: %s"%(e.__class__.__name__,e.message)
                print()
                self.help(cmd)
                sys.exit(1)
    def help(self,cmd=None):
        """Get help on commands
Usage: sixdb <cmd> <help>
        """
        cmds=['load_dir', 'update_dir', 'info',
               'da', 'da_vs_turns', 'plot_da_vs_turns',
               'mad', 'interactive','set','replace','check_results','plot_fma','plot_tune_grid']
        msg="""sixdb: command line interface of SixDeskDB
Usage: sixdb <study> <cmd> <options> or sixdb <cmd> to get additional help
        """
        if cmd is None:
            print(msg)
            print("Available commands are:")
            for cmd in cmds:
                doc=getattr(self,cmd).__doc__.splitlines()[0]
                print("%-11s: %s"%(cmd,doc))
            print()
            print("To obtain help on commands type: sixdb <cmd>")
        elif cmd in cmds:
            print("%s:"%cmd, end=' ')
            print(getattr(self,cmd).__doc__)
        else:
            print("Command not found")
            print("To get all command options type: sixdb")
    def info(self,study):
       """Print basic infomation on the database.

Usage: sixdb <dbname> info
       """
       SixDeskDB(study).info()
    def da(self, study):
       """Compute DAres files from database.

Usage: sixdb <dbname> da [-force] [-nostd]
Options:
    -force Force recalculation of DA
    -nostd Do not add std column in .plot for backward compatibility
       """
       force=False
       nostd=False
       if '-force' in self.args:
          force=True
       if '-nostd' in self.args:
          nostd=True
       SixDeskDB(study).mk_da(force=force,nostd=nostd)
    def load_dir(self, study):
       """Create database from a SixDesk directory dir.

Usage: sixdb <studydir> load_dir [logname]
<studydir> is a directory that contains the sixdeskenv and sysenv
files, e.g. ~/w1/sixjobs or ~/w1/sixjobs/studies/job_tracking.
[logname] add logging name for importing data of another user."""
       if len(self.args)>2:
          logname=self.args[2]
       else:
          logname=None
       print(logname)
       SixDeskDB.from_dir(study, logname=logname)
    def update_dir(self, study):
       """Update results from directory tree"""
       db = SixDeskDB(study)
       db.st_mad6t_run()
       db.st_mad6t_run2()
       db.st_mad6t_results()
       db.st_six_beta()
       db.st_six_input()
    def check(self, study):
       """Perform checks. Options:
zeroda:  Check whether da analysis produce 0 values of DA
       """
       db=SixDeskDB(study)
       if len(self.args)==0:
          print("Please select the check")
       else:
          getattr(db,"check_%s")(self.args[0])
    def mad(self, study):
       """Analyse the output of mad6t (HL-LHC specific)

Usage: sixdb <dbname> mad"""
       SixDeskDB(study).mad_out()
    def check_results(self, study):
       """Check results are consistent following euristic rules

Usage: sixdb <dbname> check_results"""
       noproblem=SixDeskDB(study).check_results()
       if noproblem is False:
          sys.exit(1)
    def da_vs_turns(self, study):
       """Create table da_vst for DA versus turns
       analysis.

Usage: sixdb <dbname> da_vs_turns
    Options:
    -force         : force to recalculate the da vs turns
    -turnstep      : steps in the number of turns (default: 100)
    -tmax          : maximum number of turns
                     (default: max. number of turns tracked)
    -outfile       : survival data is saved in DAsurv.out
                     and the da vs turns in DA.out
    -outfileold    : da vs turns is saved in DAold.out with the
                     old data format
    -fit           : fit the da vs turns data assuming the model:
                        D(N)=Dinf+b0/[log(N^(exp(-b1)))]^kappa
                     As this is an asumptotic rule, the first
                     ndrop data points of the da vs turns are
                     omitted.
                     default data:  dawsimp
                     default error: dawsimperr
                     default ndrop: 25
    -fitopt <data> <error> <ndrop> <skap> <ekap> <dkap>:
                     specify the data, ndrop and the scan range
                     for the scan over kappa to be used for the
                     fit of the da vs turns
                     For <error>='none' the errors of the data
                     are not taken into account
    -emit <epsilon_x> <epsilon_y>:
                     run the analysis with unequal emittances
                     in x and y
    -outfilefit    : save da vs turns fit data in DAfit.out"""
       args = self.args
       try:
         db = SixDeskDB(study, verbose=self.verbose)
       except ValueError:
         print('Error in da_vs_turns: database not found!')
         sys.exit(1)
       # define default values
       force      = False
       turnstep   = 100
       outfile    = False
       outfileold = False
       outfilefit = False
       davstfit   = False
       fitdat     = 'dawsimp'
       fitdaterr  = 'dawsimperr'
       fitndrop   = 25
       fitskap    = -5.0
       fitekap    = 5.0
       fitdkap    = 0.01
       if '-force' in args:      force=True
       if '-turnstep' in args:   turnstep=args[args.index('-turnstep')+1]
       if '-outfile' in args:    outfile=True
       if '-outfileold' in args: outfileold=True
       if '-outfilefit' in args: outfilefit=True
       if '-fit' in args:        davstfit=True
       if '-fitopt' in args:
         davstfit=True
         fitdat    = args[args.index('-fitopt') + 1]
         fitdaterr = args[args.index('-fitopt') + 2]
         fitndrop  = args[args.index('-fitopt') + 3]
         fitskap   = args[args.index('-fitopt') + 4]
         fitekap   = args[args.index('-fitopt') + 5]
         fitdkap   = args[args.index('-fitopt') + 6]
       if '-emit' in args:
         davstuemi=True                                 # option for unequal emittances
         emitx        = args[args.index('-emit') + 1]     # horizontal emittance
         emity        = args[args.index('-emit') + 2]     # vertical emittance
         # emitx, emity = float(emitx), float(emity)      # convert to float
         if self.verbose:
           print("UNEQUAL EMITTANCES REQUESTED")
       else:
         emitx, emity = None, None  # set to zero if the emittance option is not selected

       RunDaVsTurns(db, force, outfile, outfileold, turnstep, davstfit, fitdat, fitdaterr,
                    fitndrop, fitskap, fitekap, fitdkap, outfilefit, emitx, emity, 
                    verbose=self.verbose)

    def plot_fma(self, study):
      """Plot FMA.

Usage: sixdb <dbname> plot_fma
    Info: Plots the footprint if one inputfile is found in fma_sixtrack.gz, or frequency maps in frequency domain and configuration space if two inputfiles with the same method are detected. User-defined inputfile and method are also supported.  

    Options:
    - -F                  : returns a list of all the inputfiles and methods found in fma_sixtrack.gz
    -<inputfile> <method> : option for user-defined inputfile and method to plot. 
                            example1: $sixdb ats40_62.31_60.32.db plot_fma dump1 NAFF 
                            example2: $sixdb ats40_62.31_60.32.db plot_fma dump1 NAFF dump2 NAFF 
    
      """
      args=self.args
      try:
        db=SixDeskDB(study) 
      except:
        print('Error in plot_fma: database not found!')
        return -1.
      if (args[-1] == '-F'):
        print("The inputfiles and methods found are:")
        print(db.get_db_fma_inputfile_method())
        return
      if (len(args)>2):
        ### Check if user-defined inputfile and method exist
        it = iter(args[2:])
        user_defined =  list(zip(it, it))
        if set(user_defined).issubset(db.get_db_fma_inputfile_method()):    
          PlotFMA(db, args[2:]) 
        else:
          print("ERROR: The inputfile and method are not defined. Run sixdb -F for all the possible options.")
          return -1
      else:
        PlotFMA(db) 

    def plot_tune_grid(self, study):
      """Plot grid footprint.

Usage: sixdb <dbname> plot_tune_grid
    Info: Plots the footprint in the form of a grid for a user specified inputfile and method, otherwise it uses the first inputfile and method found.  

    Options:
    - -F                  : returns a list of all the inputfiles and methods found in fma_sixtrack.gz
    
      """
      args=self.args
      try:
        db=SixDeskDB(study) 
      except:
        print('Error in plot_fma: database not found!')
        return -1.
      if (args[-1] == '-F'):
        print("The inputfiles and methods found are:")
        print(db.get_db_fma_inputfile_method())
        return
      
      if (len(args)>2):
        ### Check if user-defined inputfile and method exist
        it = iter(args[2:])
        user_defined =  list(zip(it, it))
        if set(user_defined).issubset(db.get_db_fma_inputfile_method()):    
          PlotGrid(db, args[2:]) 
        else:
          print("ERROR: The inputfile and method are not defined. Run sixdb -F for all the possible options.")
          return -1
      else:
        PlotGrid(db) 
      



    def plot_da_vs_turns(self,study):
       """Create survival and da vs turns plots.

Usage: sixdb <dbname> plot_da_vs_turns
    Options:
    -ampmaxsurv    : maximum amplitude for survival plot
                     (default: max. amp tracked)
    -amprangedavst : minimum maximum amplitude for da vs turns
                     plots (default: min. and max. amplitude tracked)
    -tmax          : maximum number of turns
                     (default: max. number of turns tracked)
    -plotdat <data> <dataerr>: choose data to be plotted
                     default: data='dawsimp' dataerr='dawsimperr'
                     you can also give a comma separated list:
                        data='dawsimp,dawtrap'
                        dataerr='dawsimperr,dawtraperr'
    -plotlog       : plot da vs turns in logscale (default: False)
    -plotfit <ndrop>: plot da vs turns fit for fitndrop=ndrop
    -comp <compdbname>: compare two studies
        -lblname: labelname to be used for <dbname>
        -complblname   : labelname to be used for <compdbname>"""
       args=self.args
       try:
         db=SixDeskDB(study)
       except ValueError:
         print('Error in da_vs_turns: database not found!')
         sys.exit(1)
       # define default values
       ampmaxsurv  = max(max(db.get_amplitudes()))
       ampmaxdavst = max(max(db.get_amplitudes()))
       ampmindavst = min(min(db.get_amplitudes()))
       tmax        = db.get_turnsl()
       ldat      = ['dawsimp']
       ldaterr   = ['dawsimperr']
       plotlog     = False
       plotfit     = False
       fitndrop    = 25
       if '-ampmaxsurv' in args: ampmaxsurv=args[args.index('-ampmaxsurv')+1]
       if '-amprangedavst' in args:
         ampmindavst=args[args.index('-amprangedavst')+1]
         ampmaxdavst=args[args.index('-amprangedavst')+2]
       if '-tmax' in args: tmax=args[args.index('-tmax')+1]
       if '-plotlog' in args: plotlog=True
       if '-plotfit' in args:
         plotfit=True
         fitndrop=args[args.index('-plotfit')+1]
       if '-plotdat' in args:
         ldat   =args[args.index('-plotdat')+1].split(",")
         ldaterr=args[args.index('-plotdat')+2].split(",")
       if '-comp' in args:
         try:
           dbcomp=SixDeskDB(args[args.index('-comp')+1])
         except ValueError:
           print(('Error in da_vs_turns: database %s not found!'%dbname))
           sys.exit(1)
         lblname=db.LHCDescrip
         complblname=dbcomp.LHCDescrip
         if '-lblname' in args:     lblname     = args[args.index('-lblname')+1]
         if '-complblname' in args: complblname = args[args.index('-complblname')+1]
         PlotCompDaVsTurns(db,dbcomp,ldat,ldaterr,lblname,complblname,ampmaxsurv,ampmindavst,ampmaxdavst,tmax,plotlog,plotfit,fitndrop)
       else:
         PlotDaVsTurns(db,ldat,ldaterr,ampmaxsurv,ampmindavst,ampmaxdavst,tmax,plotlog,plotfit,fitndrop)
    def interactive(self,study):
        """Open an IPython shell with a database loeaded as db
        Usage: sixdb <dbname> interactive
        """
        print()
        import IPython
        import matplotlib.pyplot as pl
        import numpy, scipy
        print("db=SixDeskDB('%s')\n"%study)
        db=SixDeskDB(study)
        print("""\nExample:
print db.get_col('sturns1',1,45)
db.plot_col('sturns1',1,45)
db.plot_polar_col('sturns1',1)
""")
        print()
        if hasattr(IPython,'start_ipython'):
          tk=guess_toolkit()
          IPython.start_ipython(user_ns={'db':db},argv=['--pylab=%s'%tk])
        else:
          from IPython.terminal.embed import InteractiveShellEmbed
          ipshell = InteractiveShellEmbed(user_ns={db:'db'})
          ipshell.enable_pylab()
          ipshell()
    def set(self,study):
        """Redefine environment variables
        Usage: sixdb <dbname> set <key1> <value1> ...
        """
        keys=self.args[2::2]
        values=self.args[3::2]
        if len(keys)==len(values):
             lst=list(zip(keys,values))
             SixDeskDB(study).set_variables(lst,time.time())
        else:
             print("Error: Unmatched name value arguments")
    def missing_jobs(self,study):
        """Compute missing jobs
        Usage: sixdb <dbname> missing_jobs
        """
        SixDeskDB(study).missing_jobs()
    def replace(self,study):
        """Replace strings in variables definitions
        Usage: sixdb <dbname> replace <find> <replace>"""
        old=self.args[2]
        new=self.args[3]
        SixDeskDB(study).vars_replace_all(old,new)

    def plot(self, study):
      """Generate one postprocessing plot.

    Usage: sixdb <dbname> plot <option> <seed> <angle>
    
    option being one between: averem, distance, kvar, maxslope, smear, survival """

      sd = SixDeskDB(study)
      args = self.args
      if len(args)!=5:
         print("Not enough arguments for plotting")
         sys.exit(1)

      option  = args[args.index('plot')+1]
      seed    = int(args[args.index('plot')+2])
      angle   = int(args[args.index('plot')+3])
      print(args)
      try:
        plot = getattr(plots, 'plot_{name}'.format(name=option))
      except Exception as e:
        print()
        print("Wrong plot option: %s"%name)
        sys.exit(1)

      if seed < 1 or seed > len(sd.get_seeds()):
        print('Error in plot: incorrect seed!')
        sys.exit(1)
      if angle < 0 or angle >= len(sd.get_angles()):
        print('Error in da_vs_turns: incorrect angle!')
        sys.exit(1)

      nturns=100000
      a0 = 6
      a1 = 14
      result = plot(sd, seed, angle, a0, a1, nturns)
      

if __name__=="__main__":
    import sys
    SixDB(sys.argv).run()
