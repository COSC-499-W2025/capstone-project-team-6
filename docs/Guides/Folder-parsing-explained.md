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

# Round 1 of improvements

First important thing is that now there are 2 class and several functions. 

## class DirectoryNode - used to define each node/directory.
    This allows for each node to have several properties:

    path - stores the path
    is_project - tells whether the current node/directory is considered as a project or a container
    score - hueristic score on the current node for being a project
    indicators_found - shows the list of positive and negative indicators to calculate the points
    subpoject_count - is the number of subprojects to see if the current node needs to reject its project status and pass it onto the sub folders inside it
    has_files - general check


## class ProjectHeuristics- Scoring System

### Strong Indicators (60-100 points)
| Indicator | Points | Description |
|-----------|--------|-------------|
| `.git` | 100 | Git repository root - strongest indicator |
| `package.json` | 80 | Node.js project manifest |
| `pyproject.toml` | 80 | Python project configuration |
| `Cargo.toml` | 80 | Rust project manifest |
| `go.mod` | 80 | Go module definition |
| `pom.xml` | 80 | Maven project file (Java) |
| `build.gradle` | 80 | Gradle build file (JVM) |
| `.sln` | 80 | Visual Studio solution |
| `Gemfile` | 70 | Ruby dependencies |
| `composer.json` | 70 | PHP dependencies |
| `CMakeLists.txt` | 70 | CMake build configuration |
| `.csproj` | 70 | C# project file |
| `Makefile` | 60 | GNU Make build file |
| `tsconfig.json` | 60 | TypeScript configuration |
| `setup.py` | 60 | Python package setup |

### Medium Indicators (20-60 points)
| Indicator | Points | Description |
|-----------|--------|-------------|
| `Dockerfile` | 40 | Docker container definition |
| `docker-compose.yml` | 40 | Docker multi-container setup |
| `setup.cfg` | 40 | Python setup configuration |
| `requirements.txt` | 35 | Python dependencies |
| `README.md` | 30 | Markdown documentation |
| `README.rst` | 30 | reStructuredText documentation |
| `environment.yml` | 30 | Conda environment |
| `.env.example` | 25 | Environment variables template |
| `README.txt` | 25 | Plain text documentation |
| `.github` | 25 | GitHub Actions/configs (directory) |
| `README` | 20 | Generic documentation |
| `.dockerignore` | 20 | Docker ignore rules |
| `.circleci` | 20 | CircleCI configs (directory) |

### Weak Indicators (10-25 points)
| Indicator | Points | Description |
|-----------|--------|-------------|
| `LICENSE` / `LICENSE.txt` / `LICENSE.md` | 15 | License file |
| `.editorconfig` | 15 | Editor configuration |
| `jest.config.js` | 15 | Jest testing framework |
| `pytest.ini` | 15 | Pytest configuration |
| `.gitattributes` | 10 | Git attributes |
| `.prettierrc` | 10 | Prettier code formatter |
| `.eslintrc` / `.eslintrc.js` / `.eslintrc.json` | 10 | ESLint configuration |

### Negative Indicators (-15 to -50 points)
| Indicator | Points | Description |
|-----------|--------|-------------|
| `node_modules` | -50 | Node.js dependencies (NOT project root) |
| `venv` / `.venv` / `virtualenv` / `env` | -40 | Python virtual environments |
| `__pycache__` | -30 | Python bytecode cache |
| `target` | -30 | Build output (Java/Rust) |
| `build` | -25 | Build artifacts directory |
| `dist` | -25 | Distribution files |
| `.next` | -30 | Next.js build cache |
| `.cache` | -20 | Generic cache directory |
| `coverage` / `.coverage` | -20/-15 | Test coverage data |

### Default Threshold
**50 points** - A directory needs to score at least 50 points to be considered a project root.
Can be 75 points if being strict on project identification


## DFS
Secondly the depth first search was converted into a score calculation since a calculation of the likelihood of a folder being a project depends on their sub files and folders. 

It was changed so that instead of jsut declaring that any folder that contains a file is a project it checks in reference to the heurustic if a file is likely to show that it belongs to a project root. This helps calculate the score which can then be compared with a set threshold to decide if the folder is a project or not.

## Main traversal and passes
There are 3 passes that teh program goes through when classifiing projects.

### pass 1 
This is easily the most important pass. during this pass the folder goes through a BFS and DFS (calculate score) which goes through and identifies if the folder path is a project or not.

It also includes the initial calculation of hueristics to determin if a folder is a project or not. 

Although the initial version is a depth 1 search, in the new version if a folder inside the main folder has a chance of being a subproject we mark it as a project and leave it be.

### pass 2
In this pass we count the number of sub projects in a project

### pass 3
If the number of subprojects is >= 2 then the parent project is unclassified as a project and the subdirectories become projects
If the number of subprojects is =1 then the subproject is absorbed by the parent project. 

## Output
The output will be a dictionary of paths and directory nodes so that all the paths to the different projects can easily be stored.

## Future improvements
In the future it is possible to improve this by training the hueristic with data and machine learning to better optimize the classification and scoring of files but we will not be doing this in this project as we will be focusing on the analysation of projects in more detail than extremely accurate identification. The current system seems to be good enough for the time being. 
