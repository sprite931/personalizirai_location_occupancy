{
    'name': 'PersonaliziRai Location Occupancy',
    'version': '1.0.0',
    'category': 'Warehouse',
    'summary': 'Real-time PR-1 location occupancy tracking',
    'description': '''
        Interactive grid dashboard for monitoring warehouse location occupancy.
        
        Features:
        - Real-time status: Free/Reserved/Occupied
        - 167 PR-1 locations tracked
        - Auto-refresh every 60 seconds
        - Assignment wizard
        - Historical analytics
        
        Solves the race condition problem where locations appear occupied
        but are physically empty (reserved for orders in production).
    ''',
    'author': 'PersonaliziRai',
    'website': 'https://personalizirai.bg',
    'depends': [
        'base',
        'stock',
        'sale',
        'web',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/location_occupancy_views.xml',
        'views/location_occupancy_menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
