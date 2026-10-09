# AI PI
# Welcome to the Seaglider's Secret Weapon! 

The Pacific Island Fisheries Science Center utilizes 
University of Washington's autonmous underwater glider, 
named the 'Seaglider', as part of their Uncrewed Marine Systems (UMS)
initiative. The Seaglider's near silent underwater travel makes
it a fantastic vessel for acoustic data collection, however,
there are some short comings...

The Seaglider utilizes Irridium radio networks to communicate with land. 
While Irridium radios are highly reliable, they can only handle limited
bandwidth, thus, acoustic data cannot be transmitted back to shore. 
In the past, acoustic data has been lost or missed due to the inability
to gain insight on the status of the acoustic recording device. 

The Raspberry Pi, running ai_pi, aims to mitigate these issues by
providing methods to backup data and analyze data in the field.
Ai Pi uses linux's highly reliable and robust rsync to bring 
valuable acoustic data from the WISPR's (the main acoustic recording device)
unreliable microSD cards to the Pi's solid M.2 memory bank.
The Pi leverages a YOLO 11n model to analyze a collection of
audio data in the field to provide scientists with real-time insights
that would not be conventionally acheivable without transmitting inconceivable
amounts of audio data back to land.

## In This Repository 
In this repository there three main collections of code.
### 1.
Audio analysis
### 2. 
Memory management
### 3. 
Glider interfacing


## Documentation
Documentation is provided in the /docs folder along with READMEs that 
give users a jumping off point. 

## Cheers! 
