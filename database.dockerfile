FROM postgis/postgis

RUN apt update
RUN apt install -y python3-pip
RUN pip install gdown
ENTRYPOINT docker-entrypoint.sh -c max_connections=$POSTGRES_MAX_CONNECTIONS \
    -c shared_buffers=$POSTGRES_SHARED_BUFFERS \
    -c effective_cache_size=$POSTGRES_EFFECTIVE_CACHE_SIZE \
    -c maintenance_work_mem=$POSTGRES_MAINTENANCE_WORK_MEM \
    -c checkpoint_completion_target=$POSTGRES_CHECKPOINT_COMPLETION_TARGET \
    -c wal_buffers=$POSTGRES_WAL_BUFFERS \
    -c default_statistics_target=$POSTGRES_DEFAULT_STATISTICS_TARGET \
    -c random_page_cost=$POSTGRES_RANDOM_PAGE_COST \
    -c effective_io_concurrency=$POSTGRES_EFFECTIVE_IO_CONCURRENCY \
    -c work_mem=$POSTGRES_WORK_MEM \
    -c huge_pages=$POSTGRES_HUGE_PAGES \
    -c min_wal_size=$POSTGRES_MIN_WAL_SIZE \
    -c max_wal_size=$POSTGRES_MAX_WAL_SIZE \
    -c max_worker_processes=$POSTGRES_MAX_WORKER_PROCESSES \
    -c max_parallel_workers_per_gather=$POSTGRES_MAX_PARALLEL_WORKERS_PER_GATHER \
    -c max_parallel_workers=$POSTGRES_MAX_PARALLEL_WORKERS \
    -c max_parallel_maintenance_workers=$POSTGRES_MAX_PARALLEL_MAINTENANCE_WORKERS \
    -c wal_level=$POSTGRES_WAL_LEVEL \
    -c max_wal_senders=$POSTGRES_MAX_WAL_SENDERS \
    -c fsync=$POSTGRES_FSYNC