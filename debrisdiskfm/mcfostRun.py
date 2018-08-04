import copy                         # duplicate the parameter files
import subprocess                   # run the parameter files
import os                           # change directory
import numpy as np
import shutil


from . import mcfostParameterTemplate      # create a tempalte parameter file
from glob import glob

def run_hd191089(var_names = None, var_values = None, paraPath = None, calcSED = True, calcImage = True, hash_address = True):
    """This code generates and saves the MCFOST disk(s) to `paraPath` with given input parameters. 
    The MCFOST parameters are modified from the template generated by mcfostParameterTemplate().
    
    There are 3 major sections:
    1. Fixed Parameters: parameters fixed specific for the HD 191089 disk system.
    2. Variables: parameters that vary, this section is used for MCMC modeling purposes.
    3. Parameter File for HD191089: since we have the observations for the HD 191089 system with 3 instruments (Hubble/STIS, Hubble/
       NICMOS, and Gemini/GPI, the parameter structure generated from the above two sections are duplicated to suite for these 3 instruments.
       The directly and indirectly modified parameters are: field of view, pixel size, whether to generate Stokes parameters, etc.
    
    The parameter files are then run to generate for the three instruments, and saved to hard drive.
    
    Inputs:
    1. The `var_names` are the variable parameters for Section 2, and they are MANUALLY mapped to the corresponding parameters in
    the template generated by mcfostParameterTemplate(). This step is performed to create a quick link to the template variables.
    2. The `var_values` contains the list corresponding values for `var_names`. The default value is in the folder where you run the code.
    3. `paraPath` contains the path where you'd like to save the parameter files. If `None`, it will be saved in currrent folder.
    4. `calcSED`: whether to calculate the spectral energy distribution (SED) for such system.
        Note: SED calculation takes the majority of time in this code. To save time (and if you do not focus on the SED of the system),
        you can turn this to `False` when calculating the images.
    5. `calcImage`: whether to calculate the images for such system.
        Note: before `calcImage`, you have to set `calcSED = True` for at least ONCE. Once you have the SED, you can vary the input parameters
        to generate new images.
    6. `hash_address`: whether to hash the path/address to enable parallel evaluation of different parameters by saving at different addresses.
    """
    
    param_hd191089 = mcfostParameterTemplate.generateMcfostTemplate(1, [3], 1)

    resolution_stis = 0.05078
    resolution_gpi = 14.166e-3
    resolution_nicmos = 0.07565

    ###############################################################################################
    ################################# Section 1: Fixed Parameters #################################
    ################### parameters fixed specific for the HD 191089 disk system.###################
    ###############################################################################################

    dist = 50.14
    param_hd191089['#Grid geometry and size']['row1']['n_rad'] = 35
    param_hd191089['#Maps']['row3']['distance'] = dist


    param_hd191089['#Density structure']['zone0']['row1']['gas-to-dust mass ratio'] = 0
    param_hd191089['#Density structure']['zone0']['row2']['reference radius'] = 45.3
    param_hd191089['#Density structure']['zone0']['row2']['scale height'] = 1.812
    param_hd191089['#Density structure']['zone0']['row2']['vertical profile exponent'] = 2

    param_hd191089['#Grain properties']['zone0']['species0']['row0']['Grain type'] = 'Mie'
    param_hd191089['#Grain properties']['zone0']['species1']['row0']['Grain type'] = 'Mie'
    param_hd191089['#Grain properties']['zone0']['species2']['row0']['Grain type'] = 'Mie'

    param_hd191089['#Grain properties']['zone0']['species0']['row3']['amax'] = 1e3
    param_hd191089['#Grain properties']['zone0']['species1']['row3']['amax'] = 1e3
    param_hd191089['#Grain properties']['zone0']['species2']['row3']['amax'] = 1e3

    param_hd191089['#Grain properties']['zone0']['species0']['row1']['Optical indices file'] = 'dlsi_opct.dat'
    param_hd191089['#Grain properties']['zone0']['species1']['row1']['Optical indices file'] = 'ac_opct.dat'
    param_hd191089['#Grain properties']['zone0']['species2']['row1']['Optical indices file'] = 'ice_opct.dat'

    param_hd191089['#Star properties']['star0']['row0']['Temp'] = 6440
    param_hd191089['#Star properties']['star0']['row0']['radius'] = 1.4
    param_hd191089['#Star properties']['star0']['row0']['M'] = 1.4
    param_hd191089['#Star properties']['star0']['row2']['fUV'] = 0.03


    ###############################################################################################
    ##################################### Section 2: Variables ####################################
    ############# parameters that vary, this section is used for MCMC modeling purposes ###########
    ###############################################################################################
    var_names_all = ['inc', 'PA', 'm_disk', 
                     'Rc', 'R_in', 'alpha_in', 'alpha_out', 'porosity', 
                     'fmass_0', 'fmass_1', 
                     'a_min', 'Q_powerlaw']
    var_values_all = [59.7, 70, -7, 
                     45.3, 20, 3.5,  -5, 0.95,
                    0.3, 0.3,
                    1.0, 3.5]
    if var_names is None:
        var_names = var_names_all    #The above treatment allows for small paramter searching
    if var_values is None:    
        var_values = var_values_all
    if hash_address:
        hash_string = str(hash(np.array2string(np.array(var_values)))) + str(hash(np.array2string(np.random.rand(len(var_values))))) 
        # Hash the values to shrink the size, 2nd part is additional hash values to avoid same names
        
    # The MCFOST definition of inclination and position angle is not what we have been using.

    theta = dict(zip(var_names, var_values))
    theta_all = dict(zip(var_names_all, var_values_all))

    for var_name in var_names_all:
        if var_name == 'inc':
            if var_name in var_names:
                param_hd191089['#Maps']['row1']['imin'] = 180 - round(theta[var_name], 3)
                param_hd191089['#Maps']['row1']['imax'] = 180 - round(theta[var_name], 3)
            else:
                param_hd191089['#Maps']['row1']['imin'] = 180 - round(theta_all[var_name], 3)
                param_hd191089['#Maps']['row1']['imax'] = 180 - round(theta_all[var_name], 3)
            # Convert our definition to the MCFOST definition of inclination
        elif var_name == 'PA':
            if var_name in var_names:
                param_hd191089['#Maps']['row4']['disk PA'] = 90 - round(theta[var_name], 3)
            else:
                param_hd191089['#Maps']['row4']['disk PA'] = 90 - round(theta_all[var_name], 3)
            # Convert our definition to the MCFOST definition of position angle
        elif var_name == 'm_disk':
            if var_name in var_names:
                param_hd191089['#Density structure']['zone0']['row1']['dust mass'] = 10**round(theta[var_name], 3)
            else:
                param_hd191089['#Density structure']['zone0']['row1']['dust mass'] = 10**round(theta_all[var_name], 3)
        elif var_name == 'Rc':
            if var_name in var_names:
                param_hd191089['#Density structure']['zone0']['row3']['Rc'] = round(theta[var_name], 3)
                param_hd191089['#Density structure']['zone0']['row3']['Rout'] = round(130*resolution_stis*dist, 3) # extent of the outer halo
            else:
                param_hd191089['#Density structure']['zone0']['row3']['Rc'] = round(theta_all[var_name], 3)
                param_hd191089['#Density structure']['zone0']['row3']['Rout'] = round(130*resolution_stis*dist, 3) # extent of the outer halo
        elif var_name == 'R_in':
            if var_name in var_names:
                param_hd191089['#Density structure']['zone0']['row3']['Rin'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Density structure']['zone0']['row3']['Rin'] = round(theta_all[var_name], 3)
        elif var_name == 'alpha_in':
            if var_name in var_names:
                param_hd191089['#Density structure']['zone0']['row5']['surface density exponent/alpha_in'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Density structure']['zone0']['row5']['surface density exponent/alpha_in'] = round(theta_all[var_name], 3)
        elif var_name == 'alpha_out':
            if var_name in var_names:
                param_hd191089['#Density structure']['zone0']['row5']['-gamma_exp/alpha_out'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Density structure']['zone0']['row5']['-gamma_exp/alpha_out'] = round(theta_all[var_name], 3)
        elif var_name == 'porosity':
            if var_name in var_names:
                param_hd191089['#Grain properties']['zone0']['species0']['row0']['porosity'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row0']['porosity'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row0']['porosity'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Grain properties']['zone0']['species0']['row0']['porosity'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row0']['porosity'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row0']['porosity'] = round(theta_all[var_name], 3)                  
        elif var_name == 'fmass_0':
            if var_name in var_names:
                param_hd191089['#Grain properties']['zone0']['species0']['row0']['mass fraction'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row0']['mass fraction'] = round(theta['fmass_1'], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row0']['mass fraction'] = round(1 - theta[var_name] - theta['fmass_1'], 3)
            else:
                param_hd191089['#Grain properties']['zone0']['species0']['row0']['mass fraction'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row0']['mass fraction'] = round(theta_all['fmass_1'], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row0']['mass fraction'] = round(1 - theta_all[var_name] - theta_all['fmass_1'], 3)
                
        elif var_name == 'a_min':
            if var_name in var_names:
                param_hd191089['#Grain properties']['zone0']['species0']['row3']['amin'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row3']['amin'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row3']['amin'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Grain properties']['zone0']['species0']['row3']['amin'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row3']['amin'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row3']['amin'] = round(theta_all[var_name], 3)
        elif var_name == 'Q_powerlaw':
            if var_name in var_names:
                param_hd191089['#Grain properties']['zone0']['species0']['row3']['aexp'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row3']['aexp'] = round(theta[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row3']['aexp'] = round(theta[var_name], 3)
            else:
                param_hd191089['#Grain properties']['zone0']['species0']['row3']['aexp'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species1']['row3']['aexp'] = round(theta_all[var_name], 3)
                param_hd191089['#Grain properties']['zone0']['species2']['row3']['aexp'] = round(theta_all[var_name], 3)


    ###############################################################################################
    ########################### Section 3: Parameter File for HD191089 ############################
    ######################### Instrument-specific adjusts for the system. #########################
    ###############################################################################################

    param_hd191089_stis = copy.deepcopy(param_hd191089)
    stis_width = 315
    param_hd191089_stis['#Wavelength']['row3']['stokes parameters?'] = 'F'
    param_hd191089_stis['#Maps']['row0']['nx'] = stis_width
    param_hd191089_stis['#Maps']['row0']['ny'] = stis_width
    param_hd191089_stis['#Maps']['row0']['size'] = dist * stis_width * resolution_stis

    param_hd191089_nicmos = copy.deepcopy(param_hd191089)
    nicmos_width = 139
    param_hd191089_nicmos['#Wavelength']['row3']['stokes parameters?'] = 'F'
    param_hd191089_nicmos['#Maps']['row0']['nx'] = nicmos_width
    param_hd191089_nicmos['#Maps']['row0']['ny'] = nicmos_width
    param_hd191089_nicmos['#Maps']['row0']['size'] = dist * nicmos_width * resolution_nicmos


    param_hd191089_gpi = copy.deepcopy(param_hd191089)
    gpi_width = 281
    param_hd191089_gpi['#Wavelength']['row3']['stokes parameters?'] = 'T'
    param_hd191089_gpi['#Maps']['row0']['nx'] = gpi_width
    param_hd191089_gpi['#Maps']['row0']['ny'] = gpi_width
    param_hd191089_gpi['#Maps']['row0']['size'] = dist * gpi_width * resolution_gpi

    if paraPath is None:
        paraPath = './mcfost_models/'

    if os.path.exists(paraPath):
        foldernames = glob(paraPath + 'data_[0-9]*') # glob the images only, keep the SED profile
        for foldername in foldernames:
            shutil.rmtree(foldername)         # Delete the image folders if it exists to avoid duplicated computing
    else:
        os.mkdir(paraPath)              # Create the folder if it does not exist.
        
    currentDirectory = os.getcwd()          # Get current working directory, and jump back at the end
    
    if hash_address:
        paraPath_hash = paraPath[:-1] + hash_string + '/'

        if os.path.exists(paraPath_hash):
            shutil.rmtree(paraPath_hash)
            
        os.mkdir(paraPath_hash)
        
        if calcImage and (not (calcSED)):
            subprocess.call('ln -s ' + currentDirectory +'/mcfost_models/_dust_prop_th.tmp ' + paraPath_hash + '_dust_prop_th.tmp', shell = True)
            subprocess.call('ln -s ' + currentDirectory +'/mcfost_models/data_th/ ' + paraPath_hash + 'data_th', shell = True)
            # subprocess.call('cp -r ' + paraPath + 'data_th ' + paraPath_hash + '.', shell = True)
            # subprocess.call('cp ' + paraPath + '_dust_prop_th.tmp ' + paraPath_hash + '.', shell = True)
            
        os.chdir(paraPath_hash) 
    else:
        os.chdir(paraPath)                      # Now everthing is stored in the `paraPath` folder.
    
    mcfostParameterTemplate.display_file(param_hd191089_stis, 'hd191089_stis.para')
    mcfostParameterTemplate.display_file(param_hd191089_nicmos, 'hd191089_nicmos.para')
    mcfostParameterTemplate.display_file(param_hd191089_gpi, 'hd191089_gpi.para')
    
    ###############################################################################################
    ####################################### Section 4: Run ########################################
    ############################# Run the parameters and save the outputs. ########################
    ###############################################################################################
    flag_run = 0
    if calcSED:
        try:
            if os.path.exists('./data_th/'):
                shutil.rmtree('./data_th/')
            
            flag_sed = subprocess.call('mcfost hd191089_stis.para', shell = True)

            if flag_sed == 1:
                print('SED calculation is not performed, please check conflicting folder name.')
                flag_run += flag_sed
        except:
            flag_sed = 1
            print('SED calculation is not performed, something went wrong, but not the conflicting folders.')
            flag_run += flag_sed
            pass
    if calcImage:
        try:
            flags_image = [1, 1, 1]
            flags_image[0] = subprocess.call('mcfost hd191089_stis.para -img 0.5852', shell = True)
            flags_image[1] = subprocess.call('mcfost hd191089_nicmos.para -img 1.12347', shell = True)
            flags_image[2] = subprocess.call('mcfost hd191089_gpi.para -img 1.65', shell = True)

            if sum(flags_image) > 0:
                print('Image calculation is not performed for all the three wavelengths, please check conflicting folder name(s) or non-existing SED file.')
                flag_run += sum(flags_image)
        except:
            flags_image = 1
            print('Image calculation is not performed for all the three wavelengths, something went wrong, but not the conflicting folders.')
            flag_run += flags_image
            pass
            
    os.chdir(currentDirectory)              # Go back to the top working directory

    if hash_address:
        return flag_run, hash_string
    
    return flag_run
    # return 0 if everything is performed.
    
# mcmc_wrapper_hd191089(var_names = None, var_values = None, paraPath = None, calcSED = True, calcImage = True)
# The above line is tested to see the previosu codes are working.
