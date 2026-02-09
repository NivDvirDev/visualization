function sound8_p(SourceFileName,SourcePathName,DestinationFileName, DestinationPathName)

clear functions;
close all;




%[filename, pathname]=uigetfile('*.wav','Select the MATLAB code file');
% [y2,Fs2] =audioread('D:\AudioNetworkOrder710793\ANW1437_12_Birds-Wheeling.wav');
%  SourcePathName= 'D:\AudioNetworkOrder710793\';
%  SourceFileName= 'ANW1437_12_Birds-Wheeling.wav';
fullSourceFileName = fullfile(SourcePathName, SourceFileName);
[y,Fs] =audioread(fullSourceFileName);
y = normalize(y,'range',[-0.5 0.5]);
%  y=audioNormalization_YW(y, 0.5);


song = audioplayer(y, Fs);   %data for the song rate
whilecondition = song.Running;
time=0;
a=1;
N=500;
c(N,N)=0;
colormap hsv
m=500*4;
fs=44100;
dt = 1/fs;
t = (0:m-1)/fs;
n = pow2(nextpow2(m));

t2=0:0.01:24;
r2=t2;
y2=r2.*sin(t2);
x2=r2.*cos(t2);

t3=(pi):((2*pi)/12):((2*pi)*12);
length(t3);
Goldenratio=(1+sqrt(5))/2;
r3(25)=0;
r3(1)=2;
r3(11)=r3(1);
FirstRadiusDelta =(0.5+1.1)*(pi)/12;
R = FirstRadiusDelta;
FreqIndex=0;
Freq(500)=0;
RoundFreqIndex=0;
RoundFreq(100)=0;
FourierDisplay(500)=0;
xDisplay(381)=0;
yDisplay(381)=0;
cDisplay(381)=0;


clr = {'b','r'};
cstring='bmkrygcbmkrygc';
mycolormap=0;
length(t3);
RdStart=0.015;
RdEnd=-0.09;
(-(RdStart-RdEnd)/(length(t3)));
Rd=RdStart:(-(RdStart-RdEnd)/(length(t3))):(RdEnd);
% length(Rd)

for i=12:1:length(t3);

    r3(i)=r3(i-1)+R;

    R=((1+RdStart)+Rd(i))*R;
%     exp(-i/(length(t3)-12));
%     y3(i)=r3(i)*sin(t3(i));
%     x3(i)=r3(i)*cos(t3(i));
    

    deltat=(pi)/6;
    averager3=(r3(i)+r3(i-1))/2;
    jumplong=0.45;
    sector=0:jumplong:(averager3*deltat);
    lengthsector=length(sector)-1;
%      disp(['(averager3*deltat):',num2str((averager3*deltat))])
        
    
    for i2=0:jumplong:lengthsector;   
       FreqIndex=FreqIndex+1;
       CurrentRadius=(r3(i-1)+i2*(R/lengthsector));
       CurrentAngle=(t3(i-1)+(deltat/lengthsector)*i2);
       Freq(FreqIndex)=(4*(2^( (-(3-1/3)*pi+CurrentAngle)/(2*pi) )));
       Mark='kh';
       xDisplay(FreqIndex)= CurrentRadius*cos(CurrentAngle);
       yDisplay(FreqIndex)= CurrentRadius*sin(CurrentAngle);
%       plot((averager3+R*i2/lengthsector)*cos(t3(i-1)+(deltat/lengthsector)*i2),(averager3+R*i2/lengthsector)*sin(t3(i-1)+(deltat/lengthsector)*i2),Mark,'MarkerSize',jumplong*5*10,'MarkerFaceColor',sectorcolor(i));
%          text(averager]3*cos(t3(i-1)+(deltat/lengthsector)*i2),averager3*sin(t3(i-1)+(deltat/lengthsector)*i2), [num2str(marker)]);
       hold on
    end
      
     sectorcolor(i)=round((mod(i,12)));
      if ((mod(i,12))==11);% && sectorcolor(i-1)=='y');
          RoundFreqIndex=RoundFreqIndex+1; 
          RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
%           disp(['mod(i,12):',num2str(mod(i,12))])
%           disp(['i:',num2str(i)])
%           disp(['sum(mycolormap):',num2str(sum(mycolormap))])
%           disp('---------------------------------------------------')
          mycolormap=[mycolormap(:);FreqIndex-sum(mycolormap-1)];
          
      end
% % %     plot(xDisplay,yDisplay)
end

RoundFreqIndex=RoundFreqIndex+1; 
RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
mycolormap=[mycolormap(:);(FreqIndex-sum(mycolormap))*1.5];

myjet(1,3)=0;
 for mycolormapindex=2:1:length(mycolormap);
 myjet=[myjet;hsv(mycolormap(mycolormapindex))];
 end
    myjet=myjet(2:(FreqIndex+1),1:3);
% % plot(x3,y3)
% 
% % % % %*************** open a .mat file in Matlab ************************
% folder = 'D:\mat\';  % You specify this!
% fullMatFileName = fullfile(folder,  'cDisplay_Caribbean5_R18.mat');
% load(fullMatFileName);
% 
% 
% % cd techila\lib\Matlab\
% % installsdk()
% % techilainit()
% 
%  cDisplay1
close all
 [cDisplay3AMP , cDisplay3PHAZ]=record15_P(song,y,FreqIndex,Freq);
% % [cDisplay12AMP , cDisplay12PHAZ]=record19C(song,y,FreqIndex,Freq);
close all
% 
% 
% % % %*************** save a .mat file in Matlab ************************
folder = 'D:\mat\';  % You specify this!
fullMatFileName = fullfile(folder,  'make_dataset.mat');
save(fullMatFileName,'cDisplay3AMP' , 'cDisplay3PHAZ');
% 
% 
% 
% % cDisplay12AMP_diff(size(cDisplay12AMP_R15))=0;
% % cDisplay12AMP_diff=(cDisplay12AMP_R15-cDisplay12AMP_R18);
% cDisplay12AMPiso226=iso226sute6(song,y,cDisplay3AMP,FreqIndex,Freq);
% % 2AMPiso226=iso226sute11(song,y,cDisplay12AMP,FreqIndex,Freq,mycolormap,mycolormapindex);
% % %  close all
% % %  [cDisplay12PHAZ]=recordphaz11(song,y,FreqIndex,Freq,cDisplay12AMP);
% % %  close all
% % %  playrecord14(song,y,cDisplay12AMPiso226,cDisplay12PHAZ ,xDisplay,yDisplay,myjet,Freq);
% % %  close al
% 
% 
%     DestinationPathName = 'C:\';
%     DestinationFileName =  'check_record15.avi';
    playrecord15_P(song,y,cDisplay3AMP,cDisplay3PHAZ ,xDisplay,yDisplay,myjet,Freq,DestinationFileName, DestinationPathName);
% close all
end