<Qucs Schematic 26.1.1>
<Properties>
  <View=0,0,800,600,1,0,0>
  <Grid=10,10,1>
  <DataSet=qucs_mismatch.dat>
  <DataDisplay=qucs_mismatch.dpl>
  <OpenDisplay=1>
  <Script=qucs_mismatch.m>
  <RunScript=0>
  <showFrame=0>
  <FrameText0=RF LINE DOCTOR Cross-Validation>
  <FrameText1=Case 2: Resistive Mismatch (120 Ohm)>
  <FrameText2=Date: 2026-11-13>
  <FrameText3=Rev: 1.0>
</Properties>
<Symbol>
</Symbol>
<Components>
  <Pac P1 1 80 180 18 -26 0 1 "1" 1 "50.0 Ohm" 1 "0 dBm" 0 "1 GHz" 0>
  <Ground gnd 1 80 240 0 0 0 0>
  <RLCG Line1 1 220 180 71 -26 0 0 "0.0" 0 "2.5270007212e-07" 1 "1.0108002885e-10" 1 "0.0" 0 "1.0" 1 "26.85" 0>
  <R R1 1 360 180 -26 15 1 0 "120.0 Ohm" 1 "26.85" 0 "0.0" 0 "0.0" 0 "26.85" 0>
  <Ground gnd 1 360 240 0 0 0 0>
  <.SP SP1 1 180 320 0 67 0 0 "lin" 1 "500 MHz" 1 "2500 MHz" 1 "201" 1 "no" 0 "1" 0 "2" 0>
</Components>
<Wires>
  <80 180 150 180 "" 0 0 0 "">
  <150 180 220 180 "_net0" 0 0 0 "">
  <290 180 360 180 "_net1" 0 0 0 "">
  <80 180 80 240 "" 0 0 0 "">
  <360 180 360 240 "" 0 0 0 "">
</Wires>
<Diagrams>
</Diagrams>
<Paintings>
</Paintings>
