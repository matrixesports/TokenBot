from mixpanel import Mixpanel

mp = Mixpanel('6e8340ea62ff79b774da5fdbdcad0b2d')

#Tracks an event, 'makes Transaction'
def track_action(unique_id):
    mp.track(unique_id, 'action')
