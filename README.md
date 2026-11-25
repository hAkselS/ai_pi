# AI PI
# Welcome to the Seaglider's Secret Weapon! 

The Pacific Island Fisheries Science Center (PIFSC) utilizes 
University of Washington's autonmous underwater glider, 
named the 'Seaglider', as part of their Uncrewed Marine Systems (UMS)
initiative. The Seaglider's near silent underwater travel makes
it a fantastic vessel for acoustic data collection.

The Seaglider utilizes Irridium radio networks to communicate with land. 
While Irridium radios are highly reliable, they can only handle limited
bandwidth and consume a fair portion of the Seaglider's limited power budget,
thus, acoustic data cannot be transmitted back to shore. 

The PIFSC Uncrewed Marine Systems team has integrated a Rpasberry Pi 5
onto the Seaglider to provide a method of realtime analysis onboard the Seaglider.
The Raspberry Pi, running ai_pi, aims provide immediate insight into False Killer Whale
present / absence, provide a method for data backup, and increase the available data
storage by up to 3X!

Ai Pi uses linux's highly reliable and robust rsync to bring 
valuable acoustic data from the WISPR's (the main acoustic recording device)
unreliable microSD cards to the Pi's solid M.2 memory bank.
The Pi leverages a YOLO 11n model to analyze a collection of
audio data in the field to provide scientists with real-time insights
that would not be conventionally acheivable without transmitting inconceivable
amounts of audio data back to land.

## Performance Metrics 
#### Hardware Performance Metrics
The authors of this code have measured the performance metrics in laboratory
setting using an *analog* power supply and the "time" command in Linux. The following performance metrics were recorded:
- Average time to analyze 10 minutes of audio data: 
  - Real time:      3 minutes   6 seconds
  - User time:      1 minute    34 seconds
  - System time:    0 minutes   8 seconds

- Average voltage and current draw during analysis:
  - Voltage:        5.2 Volts
  - Current:        1.2 Amps

- Energy and time to analyze 60 minutes of audio data:
    - Energy:         1.06 Watt-Hours
    - Time:           10 minutes 12 seconds (real time)

- Suggested duty cycle: 
    - Analyze 1 hour of audio per each two to three hour ascendt / descent cycle.
    - 1.06 Watt-Hours consumed
    - 10 minutes of analyziation time (memory backup not included)

#### Detection Performance Metrics
- YOLO11n summary: 
    - 181 layers, 2,590,035 parameters, 0 gradients, 6.4 GFLOPs 
(181, 2590035, 0, 6.4406016)

Note: it is incredibly easy to switch models, as the mission progresses, a better
model will likely replace the current [model](models). 


## Documentation
Documentation is provided in the /docs folder along with READMEs that 
give users a jumping off point. 

## Cheers! 
