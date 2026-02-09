function  playrecord12(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,myjet,Freq)


    
     [h3,m,c,TotalFrameNumber,FrameNumberPerSecond]=initialize(Song,y,xDisplay,yDisplay,myjet,Freq);
%       playloop(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,h3,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond);
%      makemovie(TotalFrameNumber,y,m);
      


end

function [h3,m,c,TotalFrameNumber,FrameNumberPerSecond]=initialize(Song,y,xDisplay,yDisplay,myjet,Freq)
    
     

    fs=Song.SampleRate;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m=dFrame/dt;
    [TotalSample stam]=size(y(:,1));  %Song.TotalSample; 
    TotalFrameNumber=round(TotalSample/m);
    FreqIndex=length(Freq);

    set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 1280 720]);
    zoom('off');
    
    t2=atan((yDisplay)./(xDisplay));
    t2=t2.*4.*pi./1.57+4*pi;
    t = linspace(0,8*pi,FreqIndex);
    c = 1:numel(t);      %# colors
    

            size(c)
    c=[c(:);c(:)];
    %     size(xDisplay)
    
    h3 = surface([xDisplay(:), xDisplay(:)], [yDisplay(:), yDisplay(:)], 1:1,...%[cDisplay5(:,3000), cDisplay5(:,3000)], ...
    [c(:), c(:)], 'EdgeColor','flat', 'FaceColor','none');
    size(myjet)
    myjet2=[myjet;myjet];
    %myjet2=[myjet(1:length(myjet),:);myjet(1:length(myjet),:)] ; %1-flip(myjet);
    size(myjet2)
    colormap(1-myjet );

     
    zlim([0 90]);
    az = 180;
    el = 66;
    view(az, el);
    camlight left;
    lighting phong
    h3.FaceAlpha='flat'
    h3.AlphaData=h3.ZData;
    set(gca, 'color', [0 0 0]);
    set(gca,'xtick',[],'ytick',[],'ztick',[])
    set(gca,'ZColor',[0 0 0]);
    set(gca,'YColor',[0 0 0]);
    set(gca,'XColor',[0 0 0]);
    v = get(h3,'FaceColor');    
    set(gca,'ZColor',[0 0 0]);

end

function playloop(Song,y,cDisplayAMP,cDisplayPHAZ,xDisplay,yDisplay,h3,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond)
    
 

    sample=0;
    RecordSemple=0;
    FreqIndex=length(Freq);
    xDisplaySPWhide(FreqIndex,TotalFrameNumber)=0;
    yDisplaySPWhide(FreqIndex,TotalFrameNumber)=0;
    xDisplaySPWhideCurrent(FreqIndex)=0;
    yDisplaySPWhideCurrent(FreqIndex)=0;

    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter('C:\check_record15.avi', 'Quality', 100,'AudioInputPort',true,'FrameRate',FrameNumberPerSecond);
    videoFWriter.AudioCompressor
    
    
    size(xDisplay)
    r=sqrt(xDisplay(:).^2+yDisplay(:).^2);
    index(FreqIndex)=0; 
    for i3=1:1:FreqIndex; 
       [stam, index(i3)]=min( abs(Freq./2 - Freq(i3)));
    end
    size(index)
    dr=(r(index(:))-r(:)).';
    size(dr)
    alfa=angle(complex(yDisplay(:),xDisplay(:)));

    az =0.11;
    el = 0.11;
    del=0.00015;
    i3=1:1:FreqIndex; 
    while ( sample < (TotalFrameNumber-4))% == whilecondition);
        
        RecordSemple=RecordSemple+m;
        sample=round(RecordSemple/m);
        
%        xDisplaySPWhide(:,sample)=(0.02*cDisplayPHAZ(:,sample).^2./(2000*(10).^(1/800)+3).^2.*dr(:).*sin(alfa(:)));
%        yDisplaySPWhide(:,sample)=(0.02*cDisplayPHAZ(:,sample).^2./(2000*(10).^(1/800)+3).^2.*dr(:).*cos(alfa(:)));
        xDisplaySPWhide(:,sample)=(0.02*cDisplayPHAZ(:,sample).^2./(2000*(i3(:)).^(1/800)+3).^2.*dr(:).*sin(alfa(:)));
        yDisplaySPWhide(:,sample)=(0.02*cDisplayPHAZ(:,sample).^2./(2000*(i3(:)).^(1/800)+3).^2.*dr(:).*cos(alfa(:)));
       xDisplaySPWhideCurrent(:)=0;
       yDisplaySPWhideCurrent(:)=0;
       if (sample > FrameNumberPerSecond*4);
            for i4=2:1:FrameNumberPerSecond*4; 
                xDisplaySPWhideCurrent(:)=xDisplaySPWhideCurrent(:)+xDisplaySPWhide(:,sample-i4).*exp(-round(i4/4));
                yDisplaySPWhideCurrent(:)=yDisplaySPWhideCurrent(:)+xDisplaySPWhide(:,sample-i4).*exp(-round(i4/4));
            end
       end 
       for i5=1:1:FreqIndex; 
                if (abs(xDisplaySPWhideCurrent(i5)) > (dr(i5)/2));
                    xDisplaySPWhideCurrent(i5)=(dr(i5)/2);
                end
                if (abs(yDisplaySPWhideCurrent(i5)) > (dr(i5)/2));
                    yDisplaySPWhideCurrent(i5)= (dr(i5)/2);
                end
       end
%        xDisplaySP=[xDisplay(:)-xDisplaySPWhideCurrent(:);(xDisplay(:)+xDisplaySPWhideCurrent(:))].';
%        yDisplaySP=[yDisplay(:)-yDisplaySPWhideCurrent(:);(yDisplay(:)+yDisplaySPWhideCurrent(:))].';
       xDisplaySP=[xDisplay(:);(xDisplay(:)-0.15*dr(:).*sin(alfa(:)))].';
       yDisplaySP=[yDisplay(:);(yDisplay(:)-0.15*dr(:).*cos(alfa(:)))].';

       
       
       delete(h3);
       line=real(cDisplayAMP(:,sample));
%          line(1000)
        if (sample > FrameNumberPerSecond*4);
            for i4=2:1:FrameNumberPerSecond*4; 
                line=line(:)+(real(cDisplayAMP(:,sample-i4)*exp(-round(i4/4))));
            end
        end
        
%          line(1000)
       lineA=0.2*([line(:);line(:)].');
%        lineA=5.25*([real(cDisplayAMP(:,sample)).^2;real(cDisplayPHAZ(:,sample)).^2].');
       lineB=((-1)*lineA(:));
       length_line=length(real(cDisplayAMP(:,sample)));
       lineA(length_line)=-1;
       lineB(length_line)=-1;
%        length(xDisplay)
%        length(line)
       lineA(length_line+1)=-1;
       lineB(length_line+1)=-1;
        h3 = surface([xDisplaySP(:)*1.5, [xDisplay(:);xDisplay(:)]*1.5], [yDisplaySP(:)*1.5, [yDisplay(:);yDisplay(:)]*1.5],[ lineB(:),lineA(:)], ...
        [c(:), c(:)], 'EdgeColor','flat', 'FaceColor','none','LineWidth',1,'AlignVertexCenters','on'); 

%          az = 190;
%         el = 12; %-2.5*sin(sample/50);
%         view(az, el);
        
         if (el > 0.51);
            del=del*(-1);
        end
        if (el < 0.1);
            del=del*(-1);
        end
        el = el+del; %-2.5*sin(sample/50);
%         az = az+abs(del);
%         el = 12;
        view( 180*sin(az), 90*abs(el));
        set(gca,'CameraTarget',[0 0 8]);

        set(gca,'CameraViewAngleMode','manual')
        ctarg = get(gca,'CameraTarget');
        cpos = get(gca,'CameraPosition');
        newcp = cpos - 0.60*(cpos - ctarg);
        set(gca,'CameraPosition',newcp);
          
        sample
        F=getframe(gcf);
        step(videoFWriter, F.cdata,y((m*(sample-1)+1):(m*sample)+0,:));

    end
    stop(Song)
    delete(h3);
    
    release(videoFWriter);
    close all
 
      
end
