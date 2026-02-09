function [filter_mean_diff_cDisplay3AMP,mean_diff_cDisplay3AMP]=flowAMP(cDisplay9AMP)
    n=length(cDisplay9AMP);
%     diff_cDisplay3AMP = diff(abs(cDisplay9AMP).^2/n);
    diff_cDisplay3AMP = abs(cDisplay9AMP).^2/n;
    mean_diff_cDisplay3AMP = mean(diff_cDisplay3AMP);
    
    mean_diff_cDisplay3AMP = abs(mean_diff_cDisplay3AMP);
    mean_diff_cDisplay3AMP = (mean_diff_cDisplay3AMP/max(mean_diff_cDisplay3AMP))*2;
    windowSize = 100; 
    b = (1/windowSize)*ones(1,windowSize);
    for i=1:(windowSize)
        b(round(i))=exp(-1*(i/(1*windowSize^2)));
    end
    b=b/sum(b);
    b
    sum(b)
    
    a = 1;
    zeta = 0.25;
    w0 = 3;
    numerator = 9;
    denominator = [1,1.5,9];
%     sys = tf(b,a)
    
%     filter_mean_diff_cDisplay3AMP = filter(numerator,denominator,mean_diff_cDisplay3AMP);
    filter_mean_diff_cDisplay3AMP=mean_diff_cDisplay3AMP;
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
            b
        sum(b)
        filter_mean_diff_cDisplay3AMP=circshift(filter_mean_diff_cDisplay3AMP,-30);
%     windowSize = 20;
%     b = (1/windowSize)*ones(1,windowSize);
%     filter_mean_diff_cDisplay3AMP = filter(b,a,filter_mean_diff_cDisplay3AMP);
%     windowSize = 50;
%     b = (1/windowSize)*ones(1,windowSize);
%     filter_mean_diff_cDisplay3AMP = filter(b,a,mean_diff_cDisplay3AMP);
    
    windowSize = 50;
    b = (1/windowSize)*ones(1,windowSize);
    Lfilter_mean_diff_cDisplay3AMP = filter(b,a,mean_diff_cDisplay3AMP);
    filter_mean_diff_cDisplay3AMP = filter_mean_diff_cDisplay3AMP/max(filter_mean_diff_cDisplay3AMP);
    Lfilter_mean_diff_cDisplay3AMP = Lfilter_mean_diff_cDisplay3AMP/max(Lfilter_mean_diff_cDisplay3AMP);
    wname = 'dmey';
    level = 5;
    sorh = 'h';    % Specified soft or hard thresholding
    thrSettings =  [...
    0.010923547764630 ; ...
    0.026477950363056 ; ...
    0.068700757278239 ; ...
    0.456951311275025 ; ...
    1.276905288740888   ...
    ];

% Denoise using CMDDENOISE.
%--------------------------
sigDEN = cmddenoise(mean_diff_cDisplay3AMP,wname,level,sorh,NaN,thrSettings);
    plot(1:16020,sigDEN,'r',1:16020,mean_diff_cDisplay3AMP,'g--',1:16020,filter_mean_diff_cDisplay3AMP,'b');
end