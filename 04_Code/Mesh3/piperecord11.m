function  [h3]=piperecord11(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP)


    
     [h3,ts,m,c,TotalFrameNumber,xDisplay,yDisplay,FrameNumberPerSecond, R,fig]=initializeTube(Song,y,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP);

     playloop(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,h3,ts,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond, theta, Radius, R,fig);
% %     makemovie(TotalFrameNumber,y,m);
      


end



function [h3,ts,m,C,TotalFrameNumber,xDisplay,yDisplay,FrameNumberPerSecond, R,fig]=initializeTube(Song,y,xDisplay,yDisplay,myjet,Freq, theta, Radius, cDisplay3AMP)
        

    fs=Song.SampleRate;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m=dFrame/dt;
    [TotalSample stam]=size(y(:,1))  %Song.TotalSample; 
    TotalFrameNumber=round(TotalSample/m);
    FreqIndex=length(Freq);

    set(0,'defaultfigurecolor',[0 0 0]);
    
    fig=figure('Position',[0 0 1280 720]);
    
%     zoom('off');
    % create an axes that spans the whole gui
    ah = axes('unit', 'normal', 'position', [0 0 1 1]); 
    % import the background image and show it on the axes
    bg = imread('D:\drive_E_backup\dig21.jpg'); image(bg);
    % prevent plotting over the background and turn the axis off
    set(ah,'handlevisibility','off','visible','off')
    % making sure the background is behind all the other uicontrols
    uistack(ah, 'bottom');
   
%     set(gcf,'unit','norm','position',[0 0 1 1])
    set(gca,'handlevisibility','off', 'Visible','off');
    
    
    t2=atan((yDisplay)./(xDisplay));
    t2=t2.*4.*pi./1.57+4*pi;
    t = linspace(0,8*pi,FreqIndex);
    c = 1:numel(t);      %# colors
    
%     ts = textscatter3(gca,0,0,0,"str");
%       set(gca, 'Visible','off');
%     ts.AX=ah;

    size(c)
    c=[c(:)];
    %     size(xDisplay)
    THETA_1 = 10.3; % starting angle
    E = 0.003056;
    s=2;

    InerCircel=61;
    R=linspace(0,2*pi,InerCircel);
% -1.5*(theta(:)/50.2602)
    SRadius=0;
    [u,v]=meshgrid(theta,R);
    x=(Radius+((flip(u).*0.01)).*cos(v)).*cos(u);
    y=(Radius+((flip(u).*0.01)).*cos(v)).*sin(u);
    z=((flip(theta))+(flip(u).*0.01)).*sin(v)-50;
    C=zeros(InerCircel,FreqIndex,3);
    for i=1:InerCircel;
        C(i,:,:)=myjet(:,:);
    end
    disp(['C:',num2str(size(c))]);
    
    h3 = mesh(gca,x,y,z,C,'EdgeColor','interp', 'FaceColor','none','FaceLighting','gouraud');

     
    

%     h3.YData=(Radius+((u/15)).*cos(v)).*sin(u);
    tsul=flip(u).*(0.01+0.0015*cDisplay3AMP(:,201)');
    h3.YData=(theta+(tsul).*cos(v)).*sin(u);
    h3.XData=(theta+(tsul).*cos(v)).*cos(u);
    h3.ZData=(flip(theta))+(tsul).*(sin(v))-50;
    h3.CData=C;
    % colormap(1-myjet(1:stop,:) );

    size(myjet)
    myjet2=[myjet];
    %myjet2=[myjet(1:length(myjet),:);myjet(1:length(myjet),:)] ; %1-flip(myjet);
    size(myjet2)
    colormap(1-myjet );

     
%     zlim([-45 45]);
    az = 270;
    el = 90;
    view(az, el);
    camlight HEADLIGHT;
    lighting phong;
    h3.FaceAlpha='flat';
    h3.AlphaData=h3.ZData;
%     disp(['h3.ZData:',num2str(max(h3.ZData))])
%     set(gca, 'color', [0 0 0]);
%     set(gca,'xtick',[],'ytick',[],'ztick',[])
%     set(gca,'ZColor',[0 0 0]);
%     set(gca,'YColor',[0 0 0]);
%     set(gca,'XColor',[0 0 0]);
    v = get(h3,'FaceColor');    
    
    
    h3.AmbientStrength=0.9;
    h3.EdgeAlpha=0.5;
    
    
        set(gca,'NextPlot','add');
    ts = textscatter3(gca,[0 0 0],"str");
    
    set(gca, 'Visible','off');
%         ts = 1;
%     set(gca, 'Visible','off');
    
end


function playloop(Song,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,h3,ts,m,c,TotalFrameNumber,Freq,FrameNumberPerSecond, theta, Radius, R,fig)
    
    fs=Song.SampleRate;
    dt = 1/fs;
    FrameNumberPerSecond=60;
    dFrame=1/FrameNumberPerSecond;
    m=dFrame/dt;
    [TotalSample stam]=size(y(:,1))  %Song.TotalSample; 
    TotalFrameNumber=round(TotalSample/m);
    FreqIndex=length(Freq);

    sample=0;
    RecordSemple=0;% 60*m*60*2.5;
    FreqIndex=length(Freq);
    t = 0;
    
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
    
    
    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter('D:\mat\Project\Mesh\TumHiHo.avi','AudioInputPort',true,'FrameRate',FrameNumberPerSecond);
    videoFWriter.AudioCompressor;

    TotalFrameNumber
    zlim([-55 45]);
%     zlim([0 90]);
    az =270;
    del=-0.05;
    daz=0.3;
    el = 39.95+del;
    
    SRadius=0;
    [u,v]=meshgrid(theta,R);
%    
%     Test = figure('TEST');
    u_min=min(u,[],'all');
    u_range=max(u,[],'all')-min(u,[],'all');
    V0=4.7124;
    k=1;
    omega=(2*(pi));
    sample_test=200;
    [filter_mean_diff_cDisplay3AMP]=flowAMP(cDisplay9AMP);
%     Temp_filter_mean_diff_cDisplay3AMP = round(normalize(filter_mean_diff_cDisplay3AMP,'range',[0 FreqIndex]));
    filter_mean_diff_cDisplay3AMP = normalize(filter_mean_diff_cDisplay3AMP,'range',[0.5 2.5]);
    
%         ts = textscatter3(gca,0,0,0,"str");
%     set(gca, 'Visible','off');
    
    
    while ( sample < (TotalFrameNumber-4));% == whilecondition);
        tic;
        RecordSemple=RecordSemple+m;
        sample=round(RecordSemple/m);
        t = t+dFrame;
        sample_test=sample;
       
        THETA_1 = 10.3;
        E = 0.003056;
        tsul=flip(u).*(0.01+0.0015*cDisplay9AMP(:,sample_test)');  %sample
        h3.YData=(theta+(tsul).*cos(v)).*sin(u);
        h3.XData=(theta+(tsul).*cos(v)).*cos(u);
%         h3.ZData=exp(abs(flip(theta)/48.24))*4.3+(tsul).*(sin(v))-40+(10*cos((pi/180)*el));
%         (flip(theta)/4)
        
        T=(100)*dFrame;%*dFrame);
        dT=0.5*cos(((2*pi)/(60*10))*sample)*dFrame;
        
        fdT=(1/dT);
        fT=(1/T);
        f=fT;%+0.2*cos(((2*pi)/(60*10))*mod(sample,60*10));

%         T =60*dFrame; % 1[sec]
%         lmda=1.5*(pi); %
        

        old_omega=omega;
        omega=(2*(pi)*f);
        
        
        old_k=k;
        k=omega/V0;%(2*pi)/lmda;
%         V0=omega/k;
        lmda=4.8701;%(2*pi)/k;
        V=lmda/f;
        Vg=(omega-old_omega)/(k-old_k);
        speed=70*dFrame;
        Xt=speed*filter_mean_diff_cDisplay3AMP(sample); %cos(((2*pi)/(60*10))*mod(sample,60*10));
        phaz=omega*(t+Xt)*(-1);

%         phaz=(-2*(pi)/round(T/dFrame))*mod(sample,round(T/dFrame));
        h3.ZData=(2.*sin(phaz+(u-u_min).*(lmda/u_range)))+(tsul).*(sin(v))-40+(10*cos((pi/180)*el));
        disp(['     phaz:',num2str(phaz),'     Xt:',num2str(Xt)]);
%          disp(['     t:',num2str(t),'     sample:',num2str(sample),'     AMP:',num2str(2),'  T/dFr',num2str(T/dFrame),'    omega:',num2str(omega),'    k:',num2str(k),'    f:',num2str(f),'  Vg:',num2str(Vg),'  V0:',num2str(V0),'  V:',num2str(V),'   lmda:',num2str(lmda)]);
%         r=(h3.XData.^2+h3.YData.^2).^0.5;exp(-u./26).*
        
%         h3.ZData=(exp(-Radius*0.05).*sin(3.*(Radius)+(2*(pi)/100)*mod(sample,100)))*10+(tsul).*(sin(v))-40+(10*cos((pi/180)*el));
        
%         r=(flip(Radius))./(28.5*pi);%-min(Radius);
%         phaz=(-2*(pi)/100)*mod(sample,100);
%         xr=+1*r.*sin(u-phaz);
%         yr=+1*r.*cos(u+phaz);
%         h3.ZData=(8*exp(-r/3).*((1./(1+flip(r))).*(xr.*cos(4.*r+phaz)+yr.*sin(4.*r-phaz))))+(tsul).*(sin(v))-40+(10*cos((pi/180)*el));
%           
        maxWhite=max(flip(u).*(0.001*cDisplay9AMP(:,sample_test)'),[],'all'); %sample
        h3.CData=c-flip(u).*(0.01)+flip(u).*(0.001*cDisplay9AMP(:,sample_test)')./maxWhite;%sample
%         h3.AlphaData=tsul*(-1000);
%         h3.AmbientStrength=h3.ZData;
%         Temp=Temp_filter_mean_diff_cDisplay3AMP(sample);
        ts.TextData=" "; %string(Xt);
%         ts.ColorData= [c(1,Temp,1) c(1,Temp,2) c(1,Temp,3)];
%         az = az+0.01;
%         az = 45;
%         el = el+0.00005; %-2.5*sin(sample/50);
%          if (el >= 89.95);
%             del=del*(-1);
%         end
%         if (el <= 19);
%             del=del*(-1);
%         end
%         if (sample >= (TotalFrameNumber-4)/2);
% %             el = el+del;
%             az = az+daz;
%         else
%             el=19.95+del;
%         end
%         el = el+del;%*cos(pi*el/180)
        
%          if (az >= 300);
%             daz=daz*(-1);
%         end
%         if (az <= 240);
%             daz=daz*(-1);
%         end
        
        
        
        set(gca,'XLim',[-80 80]);
          set(gca,'YLim',[-80 80]);
          el=19.95;
        view( az, el);
%         view( 180*sin(el), 90*abs(el));
%         zoom('off');

        set(gca,'CameraTarget',[0 0 -17]);
        ts.ZData=-17;

        set(gca,'CameraViewAngleMode','manual');
        ctarg = get(gca,'CameraTarget');
        cpos = get(gca,'CameraPosition');
        newcp = cpos - (0.60-0.20*sin((pi/180)*el))*(cpos - ctarg);
        set(gca,'CameraPosition',newcp+[0 0 0]);
%           set(gca,'CameraTarget',[20 0 0]);


%     figure(2);
%     A = 1:1:6217;
%     small_radius=min(Radius,[],'all');
%     big_radius=max(Radius,[],'all');
%     d_radius=(big_radius-small_radius)/6217;
%     B = small_radius:d_radius:big_radius;
%     Bsin=sin(B);
% %     plot(u(1,A),(sin(phaz+u(1,A)./(7))),'*','color','r',A,u(1,A));
%     plot(A,u(1,A),'*','color','g');
%     figure(1);
        
        sample;
        F=getframe(gcf,[0 0 1280 720]);
        step(videoFWriter,F.cdata ,y((m*(sample-1)+1):(m*sample)+0,:));
        time = toc;
        disp(['time:',num2str(time),'     sample:',num2str(sample),'     az:',num2str(az),'     el:',num2str(el),'     tsul:',num2str(max(flip(u).*(0.0015*cDisplay9AMP(:,sample)'),[],'all'))]);
        
    end
    stop(Song)
    delete(h3);
    sample
    release(videoFWriter);
    close all
 
      
end



function [mean_diff_cDisplay3AMP ]=flowAMP(cDisplay9AMP)  %filter_mean_diff_cDisplay3AMP
    n=length(cDisplay9AMP);
%     diff_cDisplay3AMP = diff(abs(cDisplay9AMP).^2/n);
    diff_cDisplay3AMP = abs(cDisplay9AMP).^2/n;
    mean_diff_cDisplay3AMP = mean(diff_cDisplay3AMP);
    
    mean_diff_cDisplay3AMP = abs(mean_diff_cDisplay3AMP);
    mean_diff_cDisplay3AMP = (mean_diff_cDisplay3AMP/max(mean_diff_cDisplay3AMP))*2;
    windowSize = 50; 
%     b = (1/windowSize)*ones(1,windowSize);
    b = ones(1,windowSize);
    for i=1:windowSize
        b(i)=(1/i);
    end
    a = 1;
    
    filter_mean_diff_cDisplay3AMP=filter(b,a,mean_diff_cDisplay3AMP);
    for i2=1:5:24;
        windowSize = 26-i2; 
        b = (1/windowSize)*ones(1,windowSize);
        for i=1:(windowSize)
            b(round(i))=1-exp(-i/windowSize);%1/i;
        end
      b=flip(b);
%         normalize(b,'range',[0 1])
        b=b/sum(b);
        
        

        filter_mean_diff_cDisplay3AMP = filter(b,a,filter_mean_diff_cDisplay3AMP);
    end
    
    filter_mean_diff_cDisplay3AMP=circshift(filter_mean_diff_cDisplay3AMP,-30);
    filter_mean_diff_cDisplay3AMP = filter_mean_diff_cDisplay3AMP/max(filter_mean_diff_cDisplay3AMP);
%     plot(1:16020,mean_diff_cDisplay3AMP,'r-',1:16020,filter_mean_diff_cDisplay3AMP,'b--');
end


