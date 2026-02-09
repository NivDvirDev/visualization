
function  [cDisplay5iso226]=iso226sute11(Fs,y,cDisplay5,FreqIndex,Freq,mycolormap,mycolormapindex)

    fs=Fs;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m=dFrame/dt;
    [TotalSample stam]=size(y(:,1));  %Song.TotalSample;
    TotalFrameNumber=round(TotalSample/m);

     cDisplay5iso226(length(cDisplay5(:,1)), TotalFrameNumber)=0;
   size(cDisplay5iso226);
    is0226ForFreq(FreqIndex)=0;
    for i=1:1:FreqIndex
           is0226ForFreq(i)=(iso226(10,Freq(i))/20);%^(1/40);
         %is0226ForFreq(i)=(iso226(20,Freq(i)))/100;%^(1/40);
%            is0226ForFreq(i)
    end
    
    
    GausRange=1200;
    GausBell_x = -GausRange:1:GausRange;
    GausBell_y = gaussmf(GausBell_x,[-(length(GausBell_x)*0.100) 0] );
  %  figure
     plot(GausBell_x,GausBell_y);
    axis([-GausRange GausRange 0 1]);
    
% %     TotalFrameNumber
% %     MeanAmp(FreqIndex)=0;
% %     for i=1:1:FreqIndex;
% %         SumAmp=0;
% %         CuntAmp=0.0001;
% %         for j=1:1:TotalFrameNumber;
% %             if (cDisplay5(i,j) > 0.5);  
% %                SumAmp=SumAmp+cDisplay5(i,j);
% %                CuntAmp=CuntAmp+1;
% %             end
% %         end
% %         MeanAmp(i)=SumAmp/CuntAmp;
% %     end
% %     CircleAmp(12)=0;
% %     for i=3:1:mycolormapindex-1;
% % %         i
% % %         size(MeanAmp)
% % %         sum(mycolormap(2:i,1))
% % %         sum(mycolormap(2:(i-1),1))
% % %         max(MeanAmp(1,6783:7704))
% %         CircleAmp(i)=max(MeanAmp(sum(mycolormap(2:(i-1),1)):sum(mycolormap(2:i,1))))
% %     end
% %     Fnorm = 10/(fs/2);
% %     df = designfilt('lowpassiir',...
% %                'PassbandFrequency',Fnorm,...
% %                'FilterOrder',7,...
% %                'PassbandRipple',2,...
% %                'StopbandAttenuation',60);
% %     windowSize = 5;
% %     b = (1/windowSize)*ones(1,windowSize);
% %     subplot(3,1,1);
% %     plot(Freq,filter(b,1,MeanAmp))
% %     windowSize = 4000;
% %     b = (1/windowSize)*ones(1,windowSize); 
% %     subplot(3,1,2);
% %     plot(CircleAmp)
% %     subplot(3,1,3);
% %     plot(MeanAmp)
    
    
%         cDisplay5iso226(1,j)=-1;
%         for i=2:GausRange;  %761;
%             cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i))*GausBell_y(i))^(1/3);%(1-(GausBell_y(762-i)-GausBell_y(1))^2);
%           %  cDisplay5iso226(i,j)=((exp(cDisplay5(i,j)*GausBell_y(i))-1)*(is0226ForFreq(i)))^(1/2);
%         end
%         for i=GausRange:1:FreqIndex-GausRange-1;
%         %  is0226ForFreq=iso226(40,Freq(i));
%           cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i)))^(1);%/10^26;%))/1000;
%          % cDisplay5iso226(i,j)=((exp(1)-log(cDisplay5(i,j))));%*(is0226ForFreq(i)))
%         end
%        for i=FreqIndex-(3*GausRange)+1:FreqIndex-1;  %761;
%            
%            cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i))*GausBell_y(round((FreqIndex-i)/3)+1)^(1/18))^(1/3);%(1-(GausBell_y(762-i)-GausBell_y(1))^2);
%            if (cDisplay5iso226(i,j) > 20);
%                cDisplay5iso226(i,j)=5;
%             end
%           %  cDisplay5iso226(i,j)=((exp(cDisplay5(i,j)*GausBell_y(i))-1)*(is0226ForFreq(i)))^(1/2);
%         end
%        cDisplay5iso226(FreqIndex,j)=-1;
%     end
    
    [SmootheA]=CreateSmoothePart(GausRange,round(GausRange+(FreqIndex-(4*GausRange)-1)/3),(1/5),0.7);
    [SmootheB]=CreateSmoothePart(round(GausRange+(FreqIndex-(4*GausRange)-1)/3),round(GausRange+(FreqIndex-(4*GausRange)-1)*2/3),0.7,1.5);
    [SmootheC]=CreateSmoothePart(round(GausRange+(FreqIndex-(4*GausRange)-1)*2/3),(GausRange+(FreqIndex-(4*GausRange)-1)),1.5,12.3);
%     LongSmoothe=length(GausRange:round(GausRange+(FreqIndex-(4*GausRange)-1)/3))
%     Smoothe=(1/5):((0.5-1/5)/LongSmoothe):0.5

    for j=1:1:(TotalFrameNumber-26)
%         j
        cDisplay5iso226(1,j)=-1;
        for i=2:GausRange  %761;
            cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i))*GausBell_y(i))^(1/5);%(1-(GausBell_y(762-i)-GausBell_y(1))^2);
          %  cDisplay5iso226(i,j)=((exp(cDisplay5(i,j)*GausBell_y(i))-1)*(is0226ForFreq(i)))^(1/2);
        end
        for i=GausRange:1:round(GausRange+(FreqIndex-(4*GausRange)-1)/3)
        %  is0226ForFreq=iso226(40,Freq(i));
          cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i)))^(SmootheA(i-GausRange+1));%/10^26;%))/1000;
         % cDisplay5iso226(i,j)=((exp(1)-log(cDisplay5(i,j))));%*(is0226ForFreq(i)))
        end
        for i=round(GausRange+(FreqIndex-(4*GausRange)-1)/3):1:round(GausRange+(FreqIndex-(4*GausRange)-1)*2/3)
        %  is0226ForFreq=iso226(40,Freq(i));
          cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i)))^(SmootheB(1+i-round(GausRange+(FreqIndex-(4*GausRange)-1)/3)));%/10^26;%))/1000;
         % cDisplay5iso226(i,j)=((exp(1)-log(cDisplay5(i,j))));%*(is0226ForFreq(i)))
        end
        for i=round(GausRange+(FreqIndex-(4*GausRange)-1)*2/3):1:(GausRange+(FreqIndex-(4*GausRange)-1))
        %  is0226ForFreq=iso226(40,Freq(i));
          cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i))+1)^(SmootheC(1+i-round(GausRange+(FreqIndex-(4*GausRange)-1)*2/3)))-1;%/10^26;%))/1000;
         % cDisplay5iso226(i,j)=((exp(1)-log(cDisplay5(i,j))));%*(is0226ForFreq(i)))
        end
        
       for i=FreqIndex-(3*GausRange)+1:FreqIndex-1  %761;
           
           cDisplay5iso226(i,j)=((exp(cDisplay5(i,j))-1)*(is0226ForFreq(i))*GausBell_y(round((FreqIndex-i)/3)+1)^(1))^(1/3);%(1-(GausBell_y(762-i)-GausBell_y(1))^2);
           if (cDisplay5iso226(i,j) > 20);
               cDisplay5iso226(i,j)=5;
            end
          %  cDisplay5iso226(i,j)=((exp(cDisplay5(i,j)*GausBell_y(i))-1)*(is0226ForFreq(i)))^(1/2);
        end
       cDisplay5iso226(FreqIndex,j)=-1;
    end
    
%     cDisplay5iso226_dif(size(cDisplay5), TotalFrameNumber)=0;
%     for j=2:1:TotalFrameNumber;
%         j
%         cDisplay5iso226(1,j)=0;
%         for i=2:1:FreqIndex;
%         %  is0226ForFreq=iso226(40,Freq(i));
%        %   cDisplay5iso226_dif(i,j) = cDisplay5iso226(i,j)*((cDisplay5iso226(i,j)-cDisplay5iso226(i,j-1))/dt);%/10^26;%))/1000;
%        dif=cDisplay5iso226(i,j)-cDisplay5iso226(i,j-1);
%        cDisplay5iso226_dif(i,j)=cDisplay5iso226(i,j);
%      %  if  (dif < 0)
%                 cDisplay5iso226_dif(i,j)=(cDisplay5iso226(i,j)^((1+dif/5))/2000)*i;
%        %   end
%         end
%        
%     end
  

% for viewloop=1:1:3600;
%      
%     viewloop
%     axes_x = 1:1:FreqIndex;
%       subplot(3,1,1);
%     plot(Freq,is0226ForFreq,axes_x,is0226ForFreq(1:FreqIndex))
%  %    axis([0 8000 0 2]);
%     subplot(3,1,2);
%    plot(Freq,cDisplay5iso226(:,viewloop))
% %     axis([200 12000 0 max(cDisplay5iso226(554:707,100))*2]);
%     axis([0 50 0 20]);
%     subplot(3,1,3);
%     plot(Freq,cDisplay5(:,viewloop))
%   %  axis([200 12000 0 max(cDisplay5(554:707,100))*2]);
%     axis([0 50 0 20]);
% %     max(cDisplay5iso226(554:707,300))
% %     max(cDisplay5iso226(554:707,300))/max(cDisplay5iso226(878:938,300));
%     pause(0.05)
% end
end
 
function  [Smoothe]=CreateSmoothePart(BeginIndex,EndIndex,BeginValue,EndValue)
    
     LongSmoothe=length(BeginIndex:EndIndex);
    Smoothe=(BeginValue):((EndValue-BeginValue)/LongSmoothe):EndValue;

end