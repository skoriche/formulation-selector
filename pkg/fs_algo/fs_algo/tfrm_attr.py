# Attribute Aggregation and Transformation
import yaml
import pandas as pd
from pathlib import Path
import fs_algo.fs_algo_train_eval as fsate
from collections.abc import Iterable

from typing import Callable
import itertools
import numpy as np
import dask.dataframe as dd
from datetime import datetime, timezone
import os
from collections import ChainMap


def read_df_ext(path_to_file: str | os.PathLike) -> pd.DataFrame:
    """Read a tabular file with an extension of csv or parquet

    :param path_to_file: file path of tabular file
    :type path_to_file: str | os.PathLike
    :raises ValueError: f-string formatting still pressent in `path_to_file`
    :raises ValueError: File could not be read as expected format
    :return: tabular dataframe of file contents
    :rtype: pd.DataFrame
    """
    path_to_file = Path(path_to_file)
    if '{' in str(path_to_file):
        raise ValueError("The following path still contains f-string formatting" +
                          f" & needs rectified:\n {path_to_file}")
    if 'csv' in path_to_file.suffix:
        df = pd.read_csv(path_to_file)
    elif 'parquet' in path_to_file.suffix:
        df = pd.read_parquet(path_to_file)
    else:
        raise ValueError("Expecting path to file containing comids to be csv or parquet file")
    return df


def _get_comids_std_attrs(path_attr_config: str | os.PathLike, 
                          likely_ds_types: list =['training','prediction'], 
                          loc_id_col: str = 'comid') -> list:
    """Retrieve comids from the standardized attribute metadata generated
      by proc.attr.hydfab R package processing

    :param path_attr_config: File path to the attribute config file
    :type path_attr_config: str | os.PathLike
    :param likely_ds_types: Very likely dataset types used in the f-string
      formated metadata filename, `path_metadata`, defaults to ['training','prediction']
    :type likely_ds_types: list, optional
    :param loc_id_col: The location ID column name in the metadata tabular file,
      defaults to 'comid'
    :type loc_id_col: str, optional
    :raises Warning: In case no comid data found. This function shouldn't be called if no data desired.
    :return: list of comids corresponding to standardized attributes
    :rtype: list
    """
    # Initialize attribute configuration class for extracting attributes
    attr_cfig = fsate.AttrConfigAndVars(path_attr_config)
    attr_cfig._read_attr_config()

    fio_attr = dict(ChainMap(*attr_cfig.attr_config.get('file_io')))

    # items in attrs_cfg_dict have already been evaluated for f-strings
    datasets = attr_cfig.attrs_cfg_dict.get('datasets') # Identify datasets of interest
    dir_base = attr_cfig.attrs_cfg_dict.get('dir_base') # Possibly used for f-string eval with path_meta
    dir_std_base = attr_cfig.attrs_cfg_dict.get('dir_std_base') # Possibly used for f-string eval with path_meta

    write_type = fio_attr.get('write_type') # Likely used for f-string eval with path_meta
    ds_type_attr = fio_attr.get('ds_type') # Likely used for f-string eval with path_meta
    # These are the likely ds type names. Check to see if files with these names also exist once defining path_meta below.
    likely_ds_types=list(set(likely_ds_types+[ds_type_attr]))

    ls_comids_attrs = list()
    for ds in datasets: # ds likely used for f-string eval with path_meta
        for ds_type in likely_ds_types: # ds_type likely used for f-string eval with path_meta
            path_meta = Path(eval(f"f'{fio_attr.get('path_meta')}'"))
            if path_meta.exists:
                print(f"Reading {path_meta}")
                df_meta = read_df_ext(path_meta)
                ls_comids_attrs = ls_comids_attrs + df_meta[loc_id_col].to_list()
    if len(ls_comids_attrs) == 0:
        raise Warning(f"Unexpectedly, no data found reading standardized metadata generated by basin attribute grabbing workflow.")
        
    return ls_comids_attrs

#%%                      CUSTOM ATTRIBUTE AGGREGATION
# Function to convert a string representing a function name into a function object
def _get_function_from_string(func_str: str) -> Callable:
    if '.' in func_str:
        module_name, func_name = func_str.rsplit('.', 1)  # Split into module and function
        module = globals().get(module_name)               # Get module object from globals()
        if module:
            func = getattr(module, func_name)             # Get function object from module
    else:
        func = eval(func_str)
    return func

def _std_attr_filepath(dir_db_attrs: str | os.PathLike,
                       comid: str,
                       attrtype:str=['attr','tfrmattr','cstmattr'][0]
                       ) -> Path:
    """Make a standardized attribute filepath

    :param dir_db_attrs: Directory path containing attribute .parquet files
    :type dir_db_attrs: str | os.PathLike
    :param comid: USGS NHDplus common identifier for a catchment
    :type comid: str
    :param attrtype: the type of attribute, defaults to 'attr'
    Options include 'attr' for a publicly-available, easily retrievable 
    attribute acquired via the R package proc.attr.hydfab
    'tfrmattr' for a transformed attribute, and 
    'cstmattr' for an attribute from a custom dataset
    :type attrtype: str, optional
    :return: Full filepath of the new attribute for a single comid
    :rtype: Path
    """
    
    new_file_name = Path(f'comid_{comid}_{attrtype}.parquet')
    new_path = Path(Path(dir_db_attrs)/new_file_name)
    return new_path

def io_std_attrs(df_new_vars: pd.DataFrame,
                    dir_db_attrs:str | os.PathLike,
                    comid:str, 
                    attrtype:str)->pd.DataFrame:
    """Write/update attributes corresponding to a single comid location

    :param df_new_vars: The new variables corresponding to a catchment
    :type df_new_vars: pd.DataFrame
    :param dir_db_attrs: Directory of attribute data
    :type dir_db_attrs: str | os.PathLike
    :param comid: USGS NHDplus common identifier for a catchment
    :type comid: str
    :param attrtype: The type of attribute data. Expected to be 'attr', 'tfrmattr', or 'cstmattr'
    :type attrtype: str
    :return: The full attribute dataframe for a given catchment
    :rtype: pd.DataFrame
    """
    if df_new_vars.shape[0] > 0:
        
        # Create the expected transformation data filepath path
        path_tfrm_comid = _std_attr_filepath(dir_db_attrs=dir_db_attrs,
                        comid=comid,
                        attrtype = 'tfrmattr')
        
        if path_tfrm_comid.exists():
            print(f"Updating {path_tfrm_comid}")
            df_exst_vars_tfrm = pd.read_parquet(path_tfrm_comid)
            # Append new variables
            df_new_vars = pd.concat([df_exst_vars_tfrm,df_new_vars]).drop_duplicates()
        else:
            print(f"Writing {path_tfrm_comid}")
        
        df_new_vars.to_parquet(path_tfrm_comid,index=False)
        
    return df_new_vars

def _subset_ddf_parquet_by_comid(dir_db_attrs: str | os.PathLike,
                                  fp_struct:str 
                                  ) -> dd.DataFrame:
    """ Read a lazy dask dataframe based on a unique filename string, 
    intended to correspond to a single location (comid) but multiple 
    should work.

    :param dir_db_attrs: Directory where parquet files of attribute data
      stored
    :type dir_db_attrs: str | os.PathLike
    :param fp_struct: f-string formatted unique substring for filename of 
    parquet file corresponding to single location, i.e. f'*_{comid}_*'
    :type fp_struct: str, optional
    :return: lazy dask dataframe of all attributes corresponding to the 
    single comid
    :rtype: dd.DataFrame
    """

    # Based on the structure of comid
    fp = list(Path(dir_db_attrs).rglob('*'+str(fp_struct)+'*') )
    if fp:
      all_attr_ddf = dd.read_parquet(fp, storage_options = None)
    else:
        all_attr_ddf = None
    return all_attr_ddf


def _sub_tform_attr_ddf(all_attr_ddf: dd.DataFrame, 
                        retr_vars: str | Iterable, 
                        func: Callable) -> float:
    """Transform attributes using aggregation function

    :param all_attr_ddf: Lazy attribute data corresponding to a single location (comid)
    :type all_attr_ddf: dd.DataFrame
    :param retr_vars: The basin attributes to retrieve and aggregate by the
      transformation function
    :type retr_vars: str | Iterable
    :param func: The function used to perform the transformation on the `retr_vars`
    :type func: Callable[[Iterable[float]]]
    :return: Aggregated attribute value
    :rtype: float
    """
    sub_attr_ddf= all_attr_ddf[all_attr_ddf['attribute'].isin(retr_vars)]
    attr_val = sub_attr_ddf['value'].map_partitions(func, meta=('value','float64')).compute()
    return attr_val

def _cstm_data_src(tform_type: str,retr_vars: str | Iterable) -> str:
    """Standardize the str representation of the transformation function
    For use in the 'data_source' column in the parquet datasets.

    :param tform_type: The transformation function, provided as a str 
    of a simple function (e.g. 'np.mean', 'max', 'sum') for aggregation
    :type tform_type: str
    :param retr_vars: The basin attributes to retrieve and aggregate by the
      transformation function
    :type retr_vars: str | Iterable
    :return: A str representation of the transformation function, with variables
    sorted by character.
    :rtype: str
    """
    # Sort the retr_vars
    retr_vars_sort = sorted(retr_vars)
    return f"{tform_type}([{','.join(retr_vars_sort)}])"


def _gen_tform_df(all_attr_ddf: dd.DataFrame, new_var_id: str,
                    attr_val:float, tform_type: str,
                    retr_vars: str | Iterable) -> pd.DataFrame:
    """Generate standard dataframe for a custom transformation on attributes
      for a single location (basin)

    :param all_attr_ddf: All attributes corresponding to a single comid
    :type all_attr_ddf: dd.DataFrame
    :param new_var_id: Name of the newly desired custom variable
    :type new_var_id: str
    :param attr_val: _description_
    :type attr_val: float
    :param tform_type: The transformation function, provided as a str 
    of a simple function (e.g. 'np.mean', 'max', 'sum') for aggregation
    :type tform_type: str
    :param retr_vars: The basin attributes to retrieve and aggregate by the
      transformation function
    :type retr_vars: str | Iterable
    :raises ValueError: When the provided dask dataframe contains more than
     one unique location identifier in the 'featureID' column.
    :return: A long-format dataframe of the new transformation variables 
    for a single location
    :rtype: pd.DataFrame
    .. seealso::
        The `proc.attr.hydfab` R package and the `proc_attr_wrap` function
        that generates the standardized attribute parquet file formats
    """
    if all_attr_ddf['featureID'].nunique().compute() != 1:
        raise ValueError("Only expecting one unique location identifier. Reconsider first row logic.")
    
    base_df=all_attr_ddf.loc[0,:].compute() # Just grab the first row of a data.frame corresponding to a  and reset the values that matter
    base_df.loc[:,'attribute'] = new_var_id
    base_df.loc[:,'value'] = attr_val
    base_df.loc[:,'data_source'] = _cstm_data_src(tform_type,retr_vars)
    base_df.loc[:,'dl_timestamp'] = str(datetime.now(timezone.utc))
    return base_df



def _retr_cstm_funcs(tfrm_cfg_attrs:dict)->dict:
    # Convert dict from attribute transform config file to dict of the following sub-dicts:

    # dict_all_cstm_vars new custom variable names
    # dict_tfrm_func function design of attribute aggregation & transformation
    # dict_tfrm_func_objs strings denoting function converted to function object
    # dict_retr_vars the standard variables (attrs) needed for each transformation 
    # Each sub-dict's key value corresponds to the new variable name

    dict_retr_vars = dict()
    ls_cstm_func = list()
    ls_all_cstm_vars = list()
    ls_tfrm_funcs = list()
    ls_tfrm_func_objs = list()
    for item in tfrm_cfg_attrs['transform_attrs']:
        for key, value in item.items():
            ls_tfrm_keys = list(itertools.chain(*[[*x.keys()] for x in value]))
            idx_tfrm_type = ls_tfrm_keys.index('tform_type')
            tfrm_types = value[idx_tfrm_type]['tform_type']
            idx_vars = ls_tfrm_keys.index('vars')
            retr_vars = value[idx_vars]['vars']
            for tform_type in tfrm_types:
                ls_tfrm_func_objs.append(_get_function_from_string(tform_type))
                ls_tfrm_funcs.append(tform_type)
                new_var_id = key.format(tform_type=tform_type)
                ls_all_cstm_vars.append(new_var_id)
                ls_cstm_func.append(_cstm_data_src(tform_type,retr_vars))
                dict_retr_vars.update({new_var_id : retr_vars})

    new_keys = list(dict_retr_vars.keys())
    
    dict_all_cstm_vars = dict(zip(new_keys,ls_all_cstm_vars))
    dict_cstm_func = dict(zip(new_keys,ls_cstm_func))
    dict_tfrm_func = dict(zip(new_keys,ls_tfrm_funcs))
    dict_tfrm_func_objs =dict(zip(new_keys,ls_tfrm_func_objs))

    return {'dict_all_cstm_vars': dict_all_cstm_vars,
            'dict_cstm_func':dict_cstm_func,
            'dict_tfrm_func':dict_tfrm_func,
            'dict_tfrm_func_objs':dict_tfrm_func_objs,
            'dict_retr_vars':dict_retr_vars}

def _id_need_tfrm_attrs(all_attr_ddf: dd.DataFrame,
                          ls_all_cstm_vars:list=None,
                          ls_all_cstm_funcs:list=None)->dict:
    # Identify which attributes should be created to achieve transformation goals
    if all_attr_ddf['featureID'].nunique().compute() != 1:
        raise ValueError("Only expecting one unique location identifier. Reconsider first row logic.")

    ls_need_vars = list()
    if ls_all_cstm_vars: 
        existing_attrs_vars = set(all_attr_ddf['attribute'].compute().unique())
        # Generate a list of custom variables not yet created for a single location based on attribute name
        ls_need_attrs = [var for var in ls_all_cstm_vars if var not in existing_attrs_vars]
        ls_need_vars = ls_need_vars + ls_need_attrs
    ls_need_funcs = list()
    if ls_all_cstm_funcs:
        # Generate a list of custom variables not yet created for a single location based on function name
        existing_src = set(all_attr_ddf['data_source'].compute().unique())
        ls_need_funcs = [var for var in ls_all_cstm_funcs if var not in existing_src]
  
    dict_need_vars_funcs = {'vars': ls_need_vars,
                            'funcs': ls_need_funcs}

    return dict_need_vars_funcs
