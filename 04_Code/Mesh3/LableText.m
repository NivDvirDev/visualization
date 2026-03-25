classdef LableText
   enumeration
      Freqs, Scientific_designation, Name, Octave_name
   end
   methods
      function tf = next(obj)
          switch obj
              case 'Freqs' 
                tf = LableText.Scientific_designation;
              case 'Scientific_designation' 
                tf = LableText.Name;
              case 'Name' 
                tf = LableText.Octave_name;
              case 'Octave_name'
                tf = LableText.Freqs;
              otherwise
                warning('Unexpected plot type. No plot created.')
          end
      end
   end
end



% s=LableText.Freqs;
        
% switch plottype
%     case 'Freqs' 
%         Solfege(note).label(octave).ts.TextData=string([num2str(Solfege(note).Freqs(octave),4),'Hz']);
%     case 'Scientific_designation' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Scientific_designation(octave));
%     case 'Name' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Name);
%     case 'Octave_name'
%         Solfege(note).label(octave).ts.TextData=string(Solfege(1).Octave_name(octave));
%     otherwise
%         warning('Unexpected plot type. No plot created.')
% end