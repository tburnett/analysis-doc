# analysis-doc
An analysis framework to create web documents

# Introduction

The use case that this framework was generated involves a data analysis situation in which there are several models, or primary reconstruction analysis of a data set, and, for each such "model", there are multiple views, which I'll call analyses.  The analysis code, typically producing figures and tables, is written as a Python class inheriting from a base class containg code to produce a web document.

The three components are then:

* a _dataset_, perhaps one of many
* a set of _models_ to represent the data in  the dataset. In my work, these are detailed fits to gamma-ray data. All models for a given dataset are in a folder, containing also a file “config.json” to specify parameters. All the files for each model are in a folder, which must contain a configuration file, with parameters used to create the model, also named "config.json“.
* A set of _analyses_ to make plots and summaries of each model. Each such produces an HTML document. An individual analysis is represented by a python module containing a class inheriting from AnalysisBase
Each analysis generates one or more plots, which correspond to functions in the class.

So there is a potential HTML document for each analysis, applied to each model. Creation of a document also generates an HTML index.

# File stucture
This system assumes that model has a corresponding folder, containing a file _config.json_ defining paramters for each model; all are subfolders of a folder grouping them together, corresponding to the dataset. This folder may also have a _config.json_, containing definions of global parameters. 
