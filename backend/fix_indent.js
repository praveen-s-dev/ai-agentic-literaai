const fs = require('fs');
const content = fs.readFileSync('reports/report_generator.py', 'utf8');
const lines = content.split('\n');

// Fix line 293 (index 292) - should have exactly 4 spaces for class method
lines[292] = '    def _generate_literature_summary(self, paper_ids: List[int], paper_analyses: Dict) -> str:';

// Fix line 295 (index 294) - should have 8 spaces
lines[294] = '        if not paper_analyses:';

// Fix line 296 (index 295) - should have 12 spaces
lines[295] = '            return "## Literature Summary\\n\\nNo detailed analyses available for the papers in this session.\\n"';

// Fix line 297 (index 296) - should have 8 spaces
lines[296] = '        ';

// Fix line 298 (index 297) - should have 8 spaces
lines[297] = '        lines = ["## Literature Summary\\n"]';

// Fix line 299 (index 298) - should have 8 spaces
lines[298] = '        ';

// Fix line 300 (index 299)
lines[299] = '        # Summary statistics';

fs.writeFileSync('reports/report_generator.py', lines.join('\n'));
console.log('Fixed indentation at line 293');