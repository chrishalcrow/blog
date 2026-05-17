Neuroscience analysis pipelines 1. organise your data
=====================================================

This post will give advice about setting up analysis pipelines for neuroscience experiments in small-to-medium sized labs. The set-up will be most useful if you're doing a repetitive experiment: something like animal behaviour where each experimental session produces similar data.

There are some impressive analysis pipeline tools out there e.g. [DataJoint](https://github.com/datajoint) and [NextFlow](https://www.nextflow.io/). These ensure that a full provenance is kept, they give you access to certain tools that are hard to implement yourself, and their output should be easy to share with other labs. But my **opinion** is that they are hard to set up and understand if you have no software background. That's not good: you want a new PhD student or masters student to see the lab's pipeline, grab a piece of it, understand it, and play with it! Let's build a pipeline that is designed to be used, to be edited and to be played with.

Throughout the notes there will be code snippets in Python, but the ideas are general.

In this post we'll focus on data organisation and the theory of making a modular data analysis pipeline. Some of the content in this post sounds obvious and simple - it's not!

Experimental organisation
-------------------------

Each Neuroscience experiment is bespoke; each has a different structure. But [BIDS](https://bids.neuroimaging.io/index.html) and [NeuroBluePrint](https://neuroblueprint.neuroinformatics.dev/latest/index.html) suggest a very generic structure consisting of subjects and sessions that I find helpful. Most experiments have several subjects: in our lab these are mice. Each subject undertakes the experiment through a series of sessions. In one of the experiments in our lab, a mouse explores an openfield arena for 30 minutes. This is a session. The mouse then gets transferred to a virtual reality system and performs a task. This is another, different session. We name the openfield sesion "openfield1" and the vr session "vrnav".

You can add more labels if you'd like. In our experiment each mouse does a series of sessions each day, so we find it useful to add a `day` label. This makes it easy to ask things like "can we check all sessions for subject 10, day 4?". For your data, a "day" tag might not help or make sense. If that's the case, just use subjects and sessions, or add a different label.

**Each experimental session must be uniquely identifiable by a simple set of ids.** In the experiment discussed above these ids are: "subject", "day", "session_type". If I ask "can I see the ephys data for the vr session of mouse 25 day 24", it's very obvious what I mean.

If your task changes over the experiment (maybe there are 6 stages of learning) you could either name the sessions differently for each stage (vrnav1, vrnav2, vrnav3, ...) or call them all vrnav and store the learning stage somewhere else. Decide now, before the experiment begins.

How to organise your raw data
-----------------------------

Spend a long time deciding and debating your file organisation and naming conventions. I promise it's worth it. Here are annoying things that you should decide: if your mouse ids include "9" and "10" should you save "9" as "9" or as "09"? If you use "subject" as an id do you want to use "subject", "sub", "Subject" or "Sub"?  Make a decision and stick to it. When our pipeline crashes or fails, the majority of problems are silly issues with file naming: it's easy to get wrong.

The golden rule of data organisation: if I ask for a piece of data, you should be able to tell me what it's called and where it is. Where should it be? Your data organisation should reflect your experimental organisation. My (and [NeuroBluePrint](https://neuroblueprint.neuroinformatics.dev/latest/index.html)s) advice: make a folder for each subject. In that folder, make a folder for each day. In that folder, make a folder for each session type. That session folder contains the raw files and these should have understandable names. Write the names so that if you move the piece of data somewhere else, you still know what it is, i.e. put the all ids in all filenames.

Overall, the raw collected data from one day in our lab looks something like this:

```
data_folder/
  sub-01/
    day-01/
      typ-openfield/
        sub-01_day-01_typ-openfield_ephys/
          * the raw ephys recording *
        sub-01_day-01_typ-openfield_bonsai_output.csv
        sub-01_day-01_typ-openfield_video.avi
      typ-vrnav/
        sub-01_day-01_typ-session-vrnav_ephys/
          * the raw ephys recording *
        sub-01_day-01_typ-vrnav_trackposition.csv
        sub-01_day-01_typ-vrnav_video.avi
        sub-01_day-01_typ-vrnav_bonsai_output.csv
```

Now that you've seen the end result, I hope you agree that it's beautiful! If your not convinced here's a few points in its favour:

1. If you've never seen the data before (maybe you're a master's student in the lab), it's easy to navigate and understand.
2. If you copy a file from your data_folder to some random folder on your computer, you won't lose track of what it is.
3. You can copy all the data from a specific mouse/day/session easily. You just copy the folder over.

Importantly, you can programatically write down the filepath using f-strings for any piece of data. Like so:

``` python
data_folder = "path/to/data/folder"
subject = 12
day = 17
session_type = "vrnav"

video_path = f"{data_folder}/sub-{subject}/day-{day}/typ-{session_type}/sub-{subject}_day-{day}_typ-{session_type}_video.avi"
```

If that looks a bit gross to you, you could make a little loading function:

``` python
def get_video_path(subject, day, session_type, data_folder = "path/to/data/folder"):
    video_path = f"{data_folder}/sub-{subject}/day-{day}/typ-{session_type}/sub-{subject}_day-{day}_typ-{session_type}_video.avi"
    return video_path

video_path = get_video_path(subject, day, session_type)
```

Or you can make a more sophisticated ([loadi](https://github.com/chrishalcrow/loadi))ng system.

Neuroscience analysis pipelines 2. organise your pipeline
=========================================================

Let's develop a pipeline for an experiment. In this experiment there is ephys data and video data. We want to spike sort the ephys data, apply deeplabcut to the video data and then synchronise the outputs. Both the ephys system and the video recording system output a list of "ttl" light pulse times which will use for syncing. 

Let's sketch out the full thing:

![A graph of our pipeline](full_pipeline.png)

Each pipeline step consists of input (blue or red), processing it using a Python script (yellow) and outputs some data. The stuff we need for future analysis is the derived data (green).

Question: where do we save this output? Answer: NOT IN THE RAW DATA FOLDER! Except for fixing bugs/naming errors, you should never touch the raw folder after it's created. NEVER!!!

My advice: repeat the structure of the raw data folder, but in a "derivatives" ([following BIDS](https://bids.neuroimaging.io/getting_started/folders_and_files/derivatives.html)) folder. For the experiment discussed above, the derivatives folder would look like:

```
derivatives_folder/
  sub-01/
    day-01/
      typ-openfield1/
        ..
      typ-vrnav/
	      ..
```

What do we name the files? The key difference between raw data and derived data is that the derivatives can depend on processing choices. For example, you might try spike sorting using [KiloSort4](https://www.nature.com/articles/s41592-024-02232-7), [Mountainsort5](https://www.sciencedirect.com/science/article/pii/S0896627317307456) and [LUPIN](https://elifesciences.org/reviewed-preprints/110588) and repeat your downstream analysis for each. So you could have several "spike sorting outputs" in your derivatives folder. To account for this, you need to add more ids to label the data.

When we get around to coding, we'll use SpikeInterface to do the spike sorting. SpikeInterface will give us an "analyzer" as output which contains the spike sorted output. Other software will give other outputs. In our lab we keep several "protocols" which correspond to algorithm choices. Hence our spike sorting output is named e.g.

```
sub-01_day-01_typ-openfield1_srt-kilosort4B_analyzer
```

Where "kilosort4B" is one of our algorithmic protocols. Again, you can make a little helper function to help get these paths

``` python
def get_sorting_analyzer_folder(
  subject, 
  day, 
  session_type, 
  sorting_protocol, 
  derivatives_folder = "path/to/data/folder"
):
    analyzer_folder = f"{derivatives_folder}/sub-{subject}/day-{day}/typ-{session_type}/sub-{subject}_day-{day}_typ-{session_type}_srt-{sorting_protocol}_analyzer"
    return analyzer_folder
```

You now think I'm completely obsessed with file naming. You are correct.

Let's write down some pseudocode for the spike sorting pipeline step. This takes in ephys data. Then does spike sorting. Then saves an analyzer.

``` python
# data in
ephys_data_path = get_ephys_data_path(subject, day, session_type)
ephys_data = load_ephys_data(ephys_data_path)

# do some processing
sorting_analyzer = do_spike_sorting(ephys_data, sorting_protocol)

# data out
sorting_analyzer_folder = get_sorting_analyzer_folder(subject, day, session_type, sorting_protocol)
sorting_analyzer.save(sorting_analyzer_folder)
```

Now all we need to do is write the `do_spike_sorting` function!

What will our DeepLabCut code look like?

``` python
# data in
video_data_path = get_video_path(subject, day, session_type)
video_data = load_video(video_data_path)

# do some processing
dlc_output = do_dlc_pose_estimation(video_data, dlc_model_name)

# data out
dlc_output_path = get_dlc_output_folder(subject, day, session_type, dlc_model_name)
save_dlc_output(dlc_output, dlc_output_path)
```

Oh - very similar to our spike sorting code!!

I hope you can see that carefully organising our data, and thinking a bit about our pipeline has led to (pseudo)code that looks very simple.

Now that we're organised, next time we'll write some code!

Neuroscience analysis pipelines 3. Write some code
==================================================

Our files are well organised, we have carefully thought about our pipeline and now it's finally time to write some code.

In this post we will write a Python script which will load ephys data, sort it, and output the sorted data. We'll call the script `sort.py` and we'll run it from the terminal like so:

uv run sort.py --sub 4 --day 5 --typ openfield1 --srt kilosort4B

If you don't know about the terminal, read this. If you've never heard of uv, read this. Uv gives you a simple way to manage your Python packaging. If you're happy with your however you do packaging, that's fine. For you: `uv run` just means `python`. 

The command above passes the _arguments_ `sub`, `day`, `typ` and `srt` to the script `sort.py`. To intercept them in the script, we need to parse them. This code implements a simple argument parsers (it's a bit boring):

``` python sort.py
from argparse import ArgumentParser

parser = ArgumentParser()

parser.add_argument("sub")
parser.add_argument("day")
parser.add_argument("typ")
parser.add_argument("srt")

parsed_args = parser.parse_args()

sub = parsed_args.sub
day = parsed_args.day
typ = parsed_args.typ
srt = parsed_args.srt

# let's print one to make sure it's working
print(f"Inputted subject is {sub}")

```

Make a file called `sort.py`. Copy the code above into `sort.py`. Run `sort.py` from the terminal and check that the code is printed as you expect.

We now want to load our ephys data, which we'll need the ephys path for. Luckily, we have some code for this:

``` python sort.py

def get_ephys_data_path():
    return ephys_data_path

ephys_data_path = get_ephys_data_path(sub, day, typ)
```

The next bit of the code is doing the actual spike sorting. You'll need to tweak this for your experiment. Below is a perfectly reasonable, if simple, spike sorting pipeline which loads in an openephys recording, sorts it with kilosort, makes a SpikeInterface sorting analyzer and computes some properties of the recording

``` python sort.py
import spikeinterface.full as si

recording = si.read_openephys(ephys_data_path)
sorting = si.run_sorter(sorter_name="kilosort4", recording=recording)

preprocessed_recording_for_postprocessing = si.bandpass_filter(si.common_reference(recording))
analyzer = si.create_sorting_analyzer(
    sorting=sorting,
    recording=preprocessed_recording_for_postprocessing,
)

analyzer.compute([])

```

and now we'll save it. We know our filepath for saving.

```
def get_analyzer_folder()
    return analyzer_folder

analyzer_folder = get_analyzer_folder()
analyzer.save_as(format="binary_folder", folder=analyzer_folder)
```

I'll now combine this into one big script. When I do this, I'll refactor a little to put the core spike sorting code into a function.

``` final_sort.py

```

The point of this post is: when your data is well organised, writing an analysis pipeline is pretty easy. You might want to read some SpikeInterface docs to tweak the pipeline to suit your needs. When you do, you'll just have to edit the `do_sorting` function. We've managed to isolate all the algorithmic complexity into one place.

Now you should try this approach on your own data! Let me know how it goes :)

Extra notes:
  - If you inherit data from someone else which is not well organised, that's ok. You just need to edit your `load_{data_type}` functions. You might need to make them quite complicated, or they could look up a `json` file which contains all data paths. The second approach is a simple version of making a _virtual data set_.
  - 
