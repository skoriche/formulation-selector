
----

# Formulation Selection Decision Support (FSDS)

**Description**:  
The formulation-selection decision support tool (FSDS) is under development.

As NOAA OWP builds the model-agnostic NextGen framework, the hydrologic modeling community will need to know how to optimally select model formulations and estimate parameter values across ungauged catchments. This problem becomes intractable when considering the unique combinations of current and future model formulations combined with the innumerable possible parameter combinations across the continent. To simplify the model selection problem, we apply an analytical tool that predicts hydrologic formulation performance (Bolotin et al., 2022, Liu et al., 2022) using community-generated data. The formulation selection decision support (FSDS) tool readily predicts how models might perform across catchments based on catchment attributes. This decision support tool is designed such that as the hydrologic modeling community generates more results, better decisions can be made on where formulations would be best suited. Here we present the baseline results on formulation selection and demonstrate how the hydrologic modeling community may participate in improving and/or using this tool.

Other things to include:

  - **Technology stack**: python. The formulation-selection decision support tool is intended to be a standalone analysis, though integration with pre-existing formulation evaluation metrics tools will eventually occur.
  - **Status**:  Preliminary development. [CHANGELOG](CHANGELOG.md)._
  - **Links to production or demo instances**
  - _Describe what sets this apart from related-projects. Linking to another doc or page is OK if this can't be expressed in a sentence or two._


**Screenshot**: If the software has visual components, place a screenshot after the description; e.g.,
N/A

## Dependencies

Describe any dependencies that must be installed for this software to work.
This includes programming languages, databases or other storage mechanisms, build tools, frameworks, and so forth.
If specific versions of other software are required, or known not to work, call that out.

## Installation

### TLDR
 - Install `proc_fsds` package
   `pip install /path/to/pkg/proc_fsds/proc_fsds/.`
 - Build a yaml config file `/sripts/eval_metrics/name_of_dataset_here/name_of_dataset_schema.yaml` (refer to this template)[https://github.com/glitt13/fsds/blob/std_catg/scripts/eval_ingest/xssa/xssa_schema.yaml)
 - Create a script that reads in the data and runs the standardization processing. [Example script here](https://github.com/glitt13/fsds/blob/std_catg/scripts/eval_ingest/xssa/proc_xssa_metrics.py)
 - Then run the following:
  ```
  cd /path/to/scripts/eval_metrics/name_of_dataset_here/
  python proc_name_of_dataset_here_metrics.py "name_of dataset_here_schema.yaml"
  ```

### 1. Install the `fsds_proc` package, which standardizes raw input data into a common format.
```
> cd /path/to/pkg/proc_fsds/proc_fsds
> pip install .
```

### 2. Build a custom model metrics data ingest
Ingesting raw data describing model metrics (e.g. KGE, NSE) from modeling simulations requires two tasks:
   1. Creating a custom configuration schema as a .yaml file
   2. Modify a dataset ingest script

We track these tasks inside `formulation-selector/scripts/eval_ingest/_name_of_raw_dataset_here_/`
#### 1. `data_schema.yaml`
The data schema yaml file contains the following fields:
 - `col_schema`:  required column mappings in the evaluation metrics dataset. These describe the column names in the raw data and how they'll map to standardized column names. 
    - for `metric_mappings` refer to the the [fsds_categories.yaml](https://github.com/glitt13/fsds/blob/std_catg/pkg/fsds_proc/fsds_proc/data/fsds_categories.yaml) 
 - `file_io`: The location of the input data and desired save location. Also specifies the save file format.
 - `formulation_metadata`: Descriptive traits of the model formulation that generated the metrics. Some of these are required fields while others are optional.
 - `references`: Optional but _very_ helplful metadata describing where the data came from.

#### 2. `proc_data_metrics.py`
The script that converts the raw data into the desired format. This performs the following tasks:
 - Read in the data schema yaml file (standardized)
 - Ingest the raw data (standardized)
 - Modify the raw data to become wide-format where columns consist of the gage id and separate columns for each formulation evaluation metric (user-developed munging)
 - Call the `fsds_proc.proc_col_schema()` to standardize the dataset into a common format (standardized function call)



## Configuration

If the software is configurable, describe it in detail, either here or in other documentation to which you link.

## Usage

### raw metrics dataset processing
  ```
  cd /path/to/scripts/eval_metrics/name_of_dataset_here/
  python proc_name_of_dataset_here_metrics.py "name_of dataset_here_schema.yaml"
  ```

## How to test the software

You may also run unit tests on `fsds_proc`:
```
> cd /path/to/formulation-selection/pkg/fsds_proc/fsds_proc/tests
> python -m unittest test_proc_eval_metrics.py
```
To assess code coverage:
```
python -m coverage run -m unittest
python -m coverage report
```

## Known issues

Document any known significant shortcomings with the software.

## Getting help

If you have questions, concerns, bug reports, etc, please file an issue in this repository's Issue Tracker.

## Getting involved

This section should detail why people should get involved and describe key areas you are
currently focusing on; e.g., trying to get feedback on features, fixing certain bugs, building
important pieces, etc.

General instructions on _how_ to contribute should be stated with a link to [CONTRIBUTING](CONTRIBUTING.md).


----

## Open source licensing info
1. [TERMS](TERMS.md)
2. [LICENSE](LICENSE)


----
## Credits and references

Bolotin, LA, Haces-Garcia F, Liao, M, Liu, Q, Frame, J, Ogden FL (2022). Data-driven Model Selection in the Next Generation Water Resources Modeling Framework. In Deardorff, E., A. Modaresi Rad, et al. (2022). [National Water Center Innovators Program - Summer Institute, CUAHSI Technical Report](https://www.cuahsi.org/uploads/library/doc/SI2022_Report_v1.2.docx.pdf), HydroShare, http://www.hydroshare.org/resource/096e7badabb44c9f8c29751098f83afa

Liu, Q, Bolotin, L, Haces-Garcia, F, Liao, M, Ogden, FL, Frame JM (2022) Automated Decision Support for Model Selection in the Nextgen National Water Model. Abstract (H45I-1503) presented at 2022 AGU Fall Meeting 12-16 Dec.
