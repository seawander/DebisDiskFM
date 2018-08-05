from . import lnprior
from . import lnlike
from . import mcfostRun
import numpy as np
import shutil

def lnpost_hd191089(var_values = None, var_names = None, path_obs = None, path_model = None, calcSED = False, hash_address = True):
    """Returns the log-posterior probability (post = prior * likelihood, thus lnpost = lnprior + lnlike)
    for a given parameter combination.
    Input:  var_values: number array, values for var_names. Refer to mcfostRun() for details. 
                'It is important that the first argument of the probability function is the position of a single walker (a N dimensional numpy array).' (http://dfm.io/emcee/current/user/quickstart/)
            var_names: string array, names of variables. Refer to mcfostRun() for details.
            path_obs: string, address where the observed values are stored.
            path_model: string, address where you would like to store the MCFOST raw models (not forwarded ones).
            calcSED: boolean, whether to calculate the SED of the system.
    Output: log-posterior probability."""
    ln_prior = lnprior.lnprior_hd191089(var_names = var_names, var_values = var_values)
    if not np.isfinite(ln_prior):
        return -np.inf
    try:
        if hash_address:
            run_flag, hash_string = mcfostRun.run_hd191089(var_names = var_names, var_values = var_values, paraPath = path_model, calcSED = calcSED, calcImage = True, hash_address = hash_address)
        else:
            run_flag = mcfostRun.run_hd191089(var_names = var_names, var_values = var_values, paraPath = path_model, calcSED = calcSED, calcImage = True, hash_address = hash_address)
    except:
        pass
        
    if not (run_flag == 0):             #run is not sucessful
        shutil.rmtree(path_model)
        return -np.inf
        
    try:
        if hash_address:
            ln_likelihood = lnlike.lnlike_hd191089(path_obs = path_obs, path_model = path_model, hash_address = hash_address, hash_string = hash_string)
        else:
            ln_likelihood = lnlike.lnlike_hd191089(path_obs = path_obs, path_model = path_model, hash_address = hash_address)
        
        return ln_prior + ln_likelihood
    except:
        shutil.rmtree(path_model)
        return -np.inf                  #loglikelihood calculation is not sucessful
    