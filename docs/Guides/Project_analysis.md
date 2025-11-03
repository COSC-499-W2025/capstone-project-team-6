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
The order/hierachy call works as follows

classify_project -> classify_file -> other methods

It is structiured this way so that the system is modular so that new file sections can be easily added. 

The classify project goes through the whole folder- every single file.
It then calls file_classify which labels each file
each file is then addded to a list of that type
a dictioary made of a string and list is passed back (file type, list of files)

classify file uses the other functions as helper functions to label a file based on their extention and directory name. In basic it is done with a series of if statements.


