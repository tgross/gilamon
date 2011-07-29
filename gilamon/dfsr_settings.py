DFSR_NAME_SPACE = 'root\\MicrosoftDfs'

DFSR_PROPERTY_ENUMS = {

    'DfsrConflictInfo':
        { 'ConflictType': ( 1,
                    [ 'Name Conflict',
                      'Remote Update Local Update Conflict',
                      'Remote Update Local Delete Conflict',
                      'Local Delete Remote Update Conflict',
                      'Remote File Delete',
                      'Remote File Does Not Exist At Initial Sync',
                      ]
                    )
          },

    'DfsrConnectionInfo':
        { 'State': ( 0,
                  [ 'Connecting',
                    'Online',
                    'Offline',
                    'In Error',
                    ]
                  )
          },

    'DfsrIdUpdateInfo':
        { 'UpdateState': ( 1,
                   [ 'SCHEDULED',
                     'RUNNING',
                     'DOWNLOADING',
                     'WAIT',
                     'BLOCKED',
                     ]
                    )
          },

    'DfsrInfo':
        { 'State': ( 0,
                 [ 'Service Starting',
                   'Service Running',
                   'Service Degraded',
                   'Service Shutting Down',
                   ]
                 )
          },

    'DfsrLocalMember':
        { 'State': ( 0,
                 [ 'Initialized',
                   'Shutting Down',
                   'In Error',
                   ]
                 )
          },

    'DfsrReplicatedFolderInfo':
        { 'State': ( 0,
                 [ 'Uninitialized',
                   'Initialized',
                   'Initial Sync',
                   'Auto Recovery',
                   'Normal',
                   'In Error',
                   ]
                 )
          },

    'DfsrSyncInfo':
        { 'State': ( 0,
                 [ 'Initialized',
                   'Connecting',
                   'In Progress',
                   'Completed',
                   'In Sync',
                   'Interrupted',
                   'In Error',
                   ]
                 ),
          'InitiationReason': ( 0,
                [ 'Schedule',
                  'Forced',
                  'Paused',
                  'ForcedUntilSync',
                  ]
                ),
          },

    'DfsrVolumeInfo':
        { 'State': ( 0,
                 [ 'Initialized',
                   'Shutting Down',
                   'In Error',
                   'Auto Recovery',
                   ]
                 )
          },
}
