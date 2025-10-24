# The approch

goal: Identify if a folder contains a project or contains several projects and needs to be split apart

Initially this will be for computer science students as thos projects are easier to find the root directory of a project

## The concept
Generally computer science projects will be in a folder with several sub folders but also atleast 1 file. 
The chance that the root node of the project only having sub folders and no files is minimal with some edge cases excluded.

We will be using this as our groups staring point and build a hueristic around it. 

The diagram below shows the basic project identification- the circles i dentify the project grouping 
![](images/project%20identification.png)


## Traversal
First we have a system that goes through the zipped folder in a breath first search and depth first search hybrid . This will allow us to go through folders as shown in the image below.

![](images/traversal.png)

Start with the purple lines, it does a DFS on the root folder where all are folders and moves through the first node(root node).
Next the red line. This shows the breath first search portion. At every breath first search we do a depth first search of height 1. This is represented by the blue line. 
Check if it is a folder, file or empty
- if folder check next location at that height. 
- if file mark the parent folder a project. all files/folders the parent folder are part of the project and have no need to be checked 
- if empty either all the contents of the  folder were gone through and the folders may be project folders or the parent folder is empty. either way go back to the breath first search marker

Then move along the breath first search.
The forth red arrow in the breath first search skips the left most branch as it is considered part of a project. 

The green arrow shows the depth first search of the middle 2 folders in the breath first search. notice how the 2nd set has 2 green arrows, this is because the first destination was a folder and the program continued searching for a file.


## Future improvements (next week goals)
In the future instead of just looking for a file, we will be checking for a specific files. 
For example: if its a computer science student the projects will most likely have src folders, .git files, .docker files, etc. This will be different for students out of computer science but our goal is primarly based on computer science students and then add other majors as additional features. 