"""Scheduler service for automated scraper jobs"""
from typing import List, Optional, Dict, Any
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.date import DateTrigger
import atexit

# Import database functions
from database import (
    get_all_schedules as db_get_all_schedules,
    get_schedule as db_get_schedule,
    add_schedule as db_add_schedule,
    update_schedule as db_update_schedule,
    delete_schedule as db_delete_schedule,
    update_schedule_last_run
)

# Global scheduler instance
scheduler = BackgroundScheduler()
scheduler.start()

# Ensure scheduler shuts down on exit
atexit.register(lambda: scheduler.shutdown())


def get_schedule(schedule_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific schedule by ID"""
    return db_get_schedule(schedule_id)


def add_schedule(schedule_data: Dict[str, Any]) -> Dict[str, Any]:
    """Add a new schedule"""
    # Add to database
    new_schedule = db_add_schedule(schedule_data)
    
    # Add to scheduler if enabled
    if new_schedule.get('enabled', True):
        add_job_to_scheduler(new_schedule)
    
    return new_schedule


def update_schedule(schedule_id: str, schedule_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Update an existing schedule"""
    # Remove old job from scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Update in database
    updated_schedule = db_update_schedule(schedule_id, schedule_data)
    
    if not updated_schedule:
        return None
    
    # Add updated job to scheduler if enabled
    if updated_schedule.get('enabled', True):
        add_job_to_scheduler(updated_schedule)
    
    return updated_schedule


def delete_schedule(schedule_id: str) -> bool:
    """Delete a schedule"""
    # Remove from scheduler
    try:
        scheduler.remove_job(schedule_id)
    except:
        pass
    
    # Delete from database
    return db_delete_schedule(schedule_id)


def get_all_schedules() -> List[Dict[str, Any]]:
    """Get all schedules"""
    return db_get_all_schedules()


def add_job_to_scheduler(schedule: Dict[str, Any]):
    """Add a job to the scheduler"""
    schedule_id = schedule['id']
    source = schedule['source']
    use_selenium = schedule.get('use_selenium', False)
    
    # Import here to avoid circular imports
    # Use a wrapper function to call run_scraper
    def run_scheduled_scraper():
        """Wrapper function to run the scraper job"""
        try:
            print(f"Running scheduled scraper job: {schedule_id} for source '{source}'")
            
            # Import here to avoid circular dependency
            import sys
            import os
            backend_dir = os.path.dirname(os.path.abspath(__file__))
            if backend_dir not in sys.path:
                sys.path.insert(0, backend_dir)
            
            from main import run_scraper
            
            # Run the scraper
            run_scraper(source, use_selenium=use_selenium)
            
            # Update last_run timestamp in database
            from datetime import datetime
            update_schedule_last_run(schedule_id, datetime.now().isoformat())
            
        except Exception as e:
            print(f"Error running scheduled scraper job {schedule_id}: {e}")
            import traceback
            traceback.print_exc()
    
    # Determine trigger based on schedule type
    schedule_type = schedule.get('schedule_type', 'interval')
    
    try:
        if schedule_type == 'interval':
            # Interval-based (e.g., every 6 hours, every day)
            interval_value = schedule.get('interval_value', 1)
            interval_unit = schedule.get('interval_unit', 'hours')  # hours, minutes, days
            
            if interval_unit == 'minutes':
                trigger = IntervalTrigger(minutes=interval_value)
            elif interval_unit == 'hours':
                trigger = IntervalTrigger(hours=interval_value)
            elif interval_unit == 'days':
                trigger = IntervalTrigger(days=interval_value)
            else:
                raise ValueError(f"Invalid interval unit: {interval_unit}")
        
        elif schedule_type == 'cron':
            # Cron-based (e.g., every day at 2 AM, every Monday at 9 AM)
            trigger = CronTrigger(
                year=schedule.get('cron_year'),
                month=schedule.get('cron_month'),
                day=schedule.get('cron_day'),
                week=schedule.get('cron_week'),
                day_of_week=schedule.get('cron_day_of_week'),
                hour=schedule.get('cron_hour'),
                minute=schedule.get('cron_minute'),
                second=schedule.get('cron_second', 0)
            )
        
        elif schedule_type == 'once':
            # Run once at a specific date/time
            run_at = schedule.get('run_at')
            if isinstance(run_at, str):
                from dateutil import parser
                run_at = parser.parse(run_at)
            trigger = DateTrigger(run_at=run_at)
        
        else:
            raise ValueError(f"Invalid schedule type: {schedule_type}")
        
        # Add job to scheduler
        scheduler.add_job(
            func=run_scheduled_scraper,
            trigger=trigger,
            id=schedule_id,
            replace_existing=True,
            name=f"Scrape {source}"
        )
        
        print(f"Added scheduled job: {schedule_id} for source '{source}'")
        
    except Exception as e:
        print(f"Error adding job to scheduler: {e}")
        import traceback
        traceback.print_exc()


def initialize_schedules():
    """Initialize all enabled schedules on startup"""
    schedules = get_all_schedules()
    for schedule in schedules:
        if schedule.get('enabled', True):
            try:
                add_job_to_scheduler(schedule)
            except Exception as e:
                print(f"Error initializing schedule {schedule.get('id')}: {e}")


def get_scheduler_status() -> Dict[str, Any]:
    """Get scheduler status"""
    jobs = scheduler.get_jobs()
    return {
        'running': scheduler.running,
        'active_jobs': len(jobs),
        'jobs': [
            {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            }
            for job in jobs
        ]
    }
