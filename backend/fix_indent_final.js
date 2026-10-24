const fs = require('fs');
const content = fs.readFileSync('reports/report_generator.py', 'utf8');
const lines = content.split('\n');

// Fix line 293 (index 292) - should have exactly 4 spaces (class method)
lines[292] = '    def _generate_literature_summary(self, paper_ids: List[int], paper_analyses: Dict) -> str:';

// Fix line 295 (index 294) - 8 spaces
lines[294] = '        if not paper_analyses:';

// Fix line 296 (index 295) - 12 spaces
lines[295] = '            return "## Literature Summary\\n\\nNo detailed analyses available for the papers in this session.\\n"';

// Fix line 297 (index 296)
lines[296] = '        ';

// Fix line 298 (index 297)
lines[297] = '        lines = ["## Literature Summary\\n"]';

// Fix line 299 (index 298)
lines[298] = '        ';

// Fix line 300 (index 299)
lines[299] = '        # Summary statistics';

// Fix duplicate line at index 294 (original line 295)
lines.splice(294, 1);

fs.writeFileSync('reports/report_generator.py', lines.join('\n'));
console.log('Fixed indentation at line 293 and removed duplicate');