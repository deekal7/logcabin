setup(
    packages=['mypkg', 'mypkg.subpkg'],
    package_dir={'mypkg': 'mypkg', 'mypkg.subpkg': 'mypkg/subpkg'},
    package_data={'mypkg': ['*.xsh'], 'mypkg.subpkg': ['*.xsh']},
)