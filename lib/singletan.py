class Singletan(type):
    def __init__(self, name, father, attr):
        self.instance = None

    def __call__(self, *args, **kwargs):
        if self.instance == None:
            self.instance = super(Singletan, self).__call__(*args,**kwargs)
        return self.instance