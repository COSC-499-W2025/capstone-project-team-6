# Project analysis with LMM
## phase 1 - File identification and catergorization

In Project analysis there is a class cledd FileClassifier

At the start it defines all the extentions that are considered for different catergaries. 

We seperate the files into 5 sections
1. Code files - .py, .js, .go 
2. Documentation files - .md, .txt, 
3. config files - .json, .env
4. tests - thsi is split into test file names and directories
5. ignored directories and files  - this list will change as we progress in the analysis

### Methods
The order/hierarchy call works as follows

classify_project -> classify_file -> other methods

It is structiured this way so that the system is modular so that new file sections can be easily added. 

The classify project goes through the whole folder- every single file.
It then calls file_classify which labels each file
each file is then addded to a list of that type
a dictioary made of a string and list is passed back (file type, list of files)

classify file uses the other functions as helper functions to label a file based on their extention and directory name. In basic it is done with a series of if statements.

to test this informally use the command in terminal 
```
python src/tests/backend_test/informal_analysis_file_identification_test.py
```

the output will be like below 
![](../images/project_traversal-informal.png)

for more formal testing there is a pytest script which has 41 tests containing logic tests and tests on the Folder. For these tests i used the Test-zip-traversal/python_project.zip as a base as it checked all basic functions needed.

to run the tests use the command 
```
pytest src/tests/backend_test/test_project_analyzer.py -v
```

to run a specific test use 
```
pytest src/tests/backend_test/test_project_analyzer.py::TestProjectClassification -v

```

The reason for each test can be gathered within the test file as everything is comment with a reason at the start of the test function.
