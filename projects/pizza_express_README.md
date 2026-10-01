## Pizza Express Retrospective

I decided to do a retrospective focusing on what I learned, problems I ran into, and future plans. I feel like that's
more interesting information than a generic README. I plan to do this for all my future school projects.

## The Spec

### Description

Create a terminal based, pizza ordering program. The goal was to teach us about branching logic. We were asked to create
variables to store user options and various price points. We were to then gather user input from the terminal, use 
branching logic to correctly cast the corresponding options data its respective variable, then output the final order.


### Requirements

- Create a terminal based pizza ordering program.
- Get user selection via terminal input.
- Store user selection and option details as various variables.
- Use branching logic to correctly cast an options data to the correct variable.
- Evenly space final order read out
- Display prices to two decimal places


## The Plan

First, I was never going to make a basic terminal app. It would have taken me five minutes and I wouldn't have learned
a thing. I've been programming for some time, and this is an introductory course. That is no reason I can't learn
something, and I decided that every project I do in this class is going to be a lesson. My previous project focus on 
linear interpolation and bitmapped graphics. For this project I decided the lesson was time management. 
I've been planning to slowly work this repository into a standalone terminal rendering library, over the course of the 
semester. 

The problem was time. There's generally a project due once a week in this course, plus this is my first semester and I
had to acclimate to college in general. I noticed a large gap in our normal project routine that would last three full 
weeks. I decided that would be the best time to start building out the primitive drawing functions, which would be the
foundation of the library. So for the last three weeks I've taught myself what I needed to know, and then I put what
I learned into practice.

## Problems

- Math I haven't learned yet. I had to self-teach some things to implement all the primitive drawing methods.
  - Ex: Circle Mid-Point required some trig I haven't gotten to in class yet.


- Adapting my old line by line glyph drawing feature to the screen buffer GKS uses.


- Figuring out a way to map the data representing various options to graphical representations.
  - Ended up with something similar to MVC. Will build something to ease the model to view translation eventually.


- Building the static UI. There should be some way to define, store, and manipulate static elements. Soon™


- Selection. Related to the model to view problems. An easier way to map data structures to selection on the front end
  would be useful.


- I built the static UI before I filled out the rest of the UI. In the future I should do it in reverse. I ended up
  having to work around max widths for text repeatedly. I didn't want to extend the UI at that point as it would 
  require moving everything else. That's a problem in and of itself, and one I'll also consider how to fix.


- I ended up making a decision early on to disallow clipping the edge of the video buffer across GKS. It was something
  I didn't think I'd want or need for this project, so I put it on the back burner. I ended up wanting to make use of
  a similar feature when I was designing the receipt feature. I wanted it to print from the bottom of the screen upward.
  I realized the easiest way would be to create a large sprite and blit it outside the buffer boundary and use linear 
  interpolation to move it upward. I didn't have the ability to do so built into GKS and was nearly out of time, so
  I had to cut it and go with a more basic feature.


- The audio portion of the project did not have the ability to work with multiple sounds.
  - I did what I needed to do to get multiple sounds going, but it's not at all what I want the audio interface to look
    like. Just not enough time. Soon™


- I had to create some really sloppy code near the end to shoehorn in static screens that didn't conform to the normal
  static UI. I just threw them outside the main loop. I also had to do the same for input for those pages because that's 
  handled inside the render loop. Its slop, but it worked and I was able to add on a couple more small features because
  I chose not to force them into the main loop.


## What I learned

- Math, new concepts in trig.
- Old school graphics algorithms. Bresenham's, Circle Mid-Point.
- **Time Management**/**Projejct Management**
  - How to write a properly scoped issue with requirements, acceptance criteria, ect.
  - How to use pull requests to close issues.
    - Feature branches. I've used them, but never with pull requests and focused issues.
  - Estimating time to completion on issues of various complexity.
