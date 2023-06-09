class NoPictureAvailableError(Exception):
    pass

class NoResponseFromTheSiteError(Exception):
    pass

class NoResponseFromPicturesPageError(Exception):
    pass

class NoResponseFromTheHolidaysPageError(Exception):
    pass

class NoResponseFromPicturesDownloadHrefError(Exception):
    pass

class ImpossibleTimeError(Exception):
    pass

class LoginRequiredError(Exception):
    pass