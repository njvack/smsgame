import datetime

from django.core.management.base import NoArgsCommand

from sampler import models

import logging
logger = logging.getLogger('smsgame')

class Command(NoArgsCommand):
    help = 'Generate and send messages that need it.'
    
    def handle_noargs(self, **options):
        logger.info('schedule_and_send_messages')
        now = options.get('now') or datetime.datetime.now()
        
        # First, we start all the taskdays that it's time to start
        for td in  models.TaskDay.waiting.for_datetime(now):
            logger.debug('Starting %s' % td)
            td.start_day(now)
        
        # Next, we end the ones that need ending
        for td in models.TaskDay.active.expiring(now):
            td.end_day(now)
        
        # grab all the active task days and make sure ppts have next
        # contacts scheduled
        for td in models.TaskDay.active.all():
            logger.debug('Running %s' % td)
            ppt = td.participant
            if ppt.next_contact_time is None:
                logger.debug("Setting next contact time for %s" % ppt)
                ppt.generate_contact_after(now)
            logger.debug("%s next contact time: %s" % 
                (ppt, ppt.next_contact_time))
        
        # Finally finally, grab all the participants with scheduled contacts
        # and have them do their contacty-magic.
        ppts = models.Participant.objects.filter(
            next_contact_time__isnull=False).filter(
            next_contact_time__lte=now)
        for ppt in ppts:
            logger.debug("%s gots a contact to make" % (ppt))
            # obj = ppt.get_next_contact_object()
            