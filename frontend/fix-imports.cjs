const fs = require('fs');
const path = require('path');

const componentsDir = path.join(__dirname, 'src', 'components');
const files = fs.readdirSync(componentsDir).filter(f => f.endsWith('.tsx'));

for (const file of files) {
    const filePath = path.join(componentsDir, file);
    let content = fs.readFileSync(filePath, 'utf8');
    const updatedContent = content.replace(/import '\.\/styles\//g, "import '../styles/");
    
    if (content !== updatedContent) {
        fs.writeFileSync(filePath, updatedContent);
        console.log(`Fixed: ${file}`);
    }
}

console.log('Done!');