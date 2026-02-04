import { spawn } from 'child_process';

console.log("Starting Python Flask app...");

const python = spawn('python', ['app.py'], { stdio: 'inherit' });

python.on('error', (err) => {
    console.error('Failed to start python process:', err);
});

python.on('close', (code) => {
  console.log(`Python process exited with code ${code}`);
  process.exit(code || 0);
});

// Handle termination signals
process.on('SIGTERM', () => {
    python.kill('SIGTERM');
});
process.on('SIGINT', () => {
    python.kill('SIGINT');
});
