# scromfyUI_Nodes

A collection of custom nodes for [ComfyUI](https://github.com/comfy-org/ComfyUI) designed with a focus on flexibility, modularity, and clean workflow management.

## Core Principles

### 1. Universal Nodes (One Node to rule them all)
I believe in **Universal Nodes** whenever possible and feasible.
- **One Node to rule them all**: You shouldn't have to switch out a key node just because you change a model type or input format.
- **Flexibility**: Workflows should be adaptable and resilient to changes in the underlying stack.

### 2. Forking and Innovation (Stand on the shoulders of giants)
This repository serves as a hub for both original ideas and refined forks.
- **Standing on Shoulders**: I often copy and fork other people's code.
- **New Directions**: Sometimes I contribute back to the original source; other times, I take the code in a completely new direction. This is where those "new direction" nodes live.
- **License**: All of my own code is released under the MIT license.  Not all of the code here originates with me, so some of the code might be covered under other licenses.  Please check the individual node files for license information.

### 3. Clean Data Management (The Scromfy Way)
Moving beyond the limitations of traditional ComfyUI data passing.
- **Beyond Spaghetti**: While Comfy Set/Get nodes can help reduce wire clutter, they can quickly lead to a different kind of mess - piles of set/gets all over the place, and then people tuck them away for a cleaner looking workflow.  This is still a mess.
- **Better Buses**: Existing "Bus" or "Pipe" implementations often fall short of being intuitive or correctly implemented, or limit you in many ways.
- **Dictionary-based Flow**: This project builds toward a better method: using **named items in a Python dictionary**. This keeps data organized, accessible, and the workflow clean.

### 4. Nodes 1.0 

While I respect the Nodes 2.0 + Comfy API v3 stuff, it's raw and broken, lots of better devs than me have found it impossible to do things they do now.  So I'm sticking with the tried and true for now.  If ports or upgrades happen, that'll be a new repo.  Consider this stuff Nodes 1.0.

Thanks and Kudos:

- [ComfyUI](https://github.com/comfy-org/ComfyUI)
