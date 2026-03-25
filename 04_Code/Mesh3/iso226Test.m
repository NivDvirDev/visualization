function []=test()

% Calculate SPLs
  phons = [20:10:80];
  [spl,f] = iso226(phons,[],true);

  % plot
  figure; semilogx(f,spl)
  set(gca,'xlim',[min(f(:)) max(f(:))])
  legend(num2str(phons'),'location','southwest');
  title('Equal loudness contours for different loudness levels (in phons)')
  xlabel('Frequency [Hz]')
  ylabel('SPL [dB]')

end