const fs = require('fs');
const content = fs.readFileSync('src/components/ChatWorkspace.tsx', 'utf8');
let braceCount = 0;
let inString = false;
let stringChar = '';
let parenCount = 0;
let bracketCount = 0;

for (let i = 0; i < content.length; i++) {
  const c = content[i];
  const prev = content[i-1];
  
  if (!inString) {
    if (c === '"' || c === "'" || c === '`') {
      inString = true;
      stringChar = c;
    } else if (c === '{') {
      console.log('Open brace at pos', i, 'line:', content.substring(0, i).split('\n').length);
    } else if (c === '}') {
      console.log('Close brace at pos', i, 'line:', content.substring(0, i).split('\n').length);
    }
  } else if (c === stringChar && prev !== '\\') {
    inString = false;
  }
}
console.log('Done');