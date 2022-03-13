# Index

- [Factsim](#org1aaf524)
- [Current features](#orga5a9dc9)
- [Beware](#org344cdeb)
- [Future](#org7d7ae23)
- [How to use: Detailed example](#orgded9be0)
- [Thanks:](#orgf6bf839)


<a id="org1aaf524"></a>

# Factsim

A simulator for Factorio circuit network entities


<a id="orga5a9dc9"></a>

# Current features

-   Has a basic GUI that lets you operate the circuit and examine the entities.
-   simulates the output of different componets. The components currently implemented are: -Constant combinator -Decider combinator -Arithmetic combinator -Electric poles and substation -Lamps -Pushbuttons
-   has a factsim class that can make the components interact


<a id="org344cdeb"></a>

# Beware

-   it is not well documented (yet)


<a id="org7d7ae23"></a>

# Future

-   I'll try to add some documentation, but if you have dobts please ask, I'm very new to programming so I'm grateful for feedback.
-   I think tkinter is a bit limited as a GUI framework, ill try to get the best out of it and maybe in the future overhaul it with a different framework.


<a id="orgded9be0"></a>

# How to use: Detailed example

You need to have python 3 installed and available in your system. Go to the folder where you downloaded the Factsim.py file. Execute the tool with \`python Factsim.py\`, you will be prompted to select a file. This file must contain the blueprint string saved as plain text. Once opened, the main window will present you a diagram of your circuit, you can interact clicking on the entities to see the relevant information and you can step forward and backward the simulaiton and explore the outputs of each entity on each step.


<a id="orgf6bf839"></a>

# Thanks:

-   Thanks to the people from the fCPU mod discord, specially Mernon, for their motivation.
