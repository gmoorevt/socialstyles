def get_version_info():
    """Read version information from version.txt file."""
    try:
        import os
        version_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'version.txt')
        
        if not os.path.exists(version_file):
            return {'version': 'dev'}
            
        version_info = {'version': 'Unknown'}
        with open(version_file, 'r') as f:
            for line in f:
                if line.startswith('Version:'):
                    version_info['version'] = line.split(':', 1)[1].strip()
                    break
        
        return version_info
    except Exception:
        return {'version': 'dev'} 