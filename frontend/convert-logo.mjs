import fs from 'fs';
import potrace from 'potrace';

const inputImagePath = './public/logo.png';
const outputSvgPath = './public/logo.svg';

potrace.trace(inputImagePath, function(err, svg) {
  if (err) throw err;
  fs.writeFileSync(outputSvgPath, svg);
  console.log('Successfully converted logo.png to logo.svg');
});
