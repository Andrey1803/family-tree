import os
size = os.path.getsize('models.py')
with open('check.txt', 'w', encoding='utf-8') as f:
    f.write(f'File size: {size}\n')
    with open('models.py', 'r', encoding='utf-8', errors='replace') as mf:
        lines = mf.readlines()
        for i in range(395, 415):
            if i < len(lines):
                f.write(f'{i+1}: {lines[i][:60]}\n')
print('DONE - check check.txt')
