from api.models import Match, Sport, Selection, Market
from api.serializers import MatchListSerializer, MatchDetailSerializer
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.response import Response


class MatchViewSet(viewsets.ModelViewSet):
    """
    retrieve:
    Return the given match.
    list:
    Return a list of all the existing matches.
    create:
    Create a new match instance.
    """
    queryset = Match.objects.all()
    serializer_class = MatchListSerializer # for list view
    detail_serializer_class = MatchDetailSerializer # for detail view
    filter_backends = (DjangoFilterBackend, OrderingFilter,)
    ordering_fields = '__all__'
    def get_serializer_class(self):
        """
        Determins which serializer to user `list` or `detail`
        """
        if self.action == 'retrieve':
            if hasattr(self, 'detail_serializer_class'):
                return self.detail_serializer_class
        return super().get_serializer_class()
    def get_queryset(self):
        """
        Optionally restricts the returned queries by filtering against
        a `sport` and `name` query parameter in the URL.
        """
        queryset = Match.objects.all()
        sport = self.request.query_params.get('sport', None)
        name = self.request.query_params.get('name', None)
        if sport is not None:
            sport = sport.title()
            queryset = queryset.filter(sport__name=sport)
        if name is not None:
            queryset = queryset.filter(name=name)
        return queryset
    def create(self, request):
        """
        to parse the incoming request and create a new match or update
        existing odds.
        """
        message = request.data.pop('message_type')
        # check if incoming api request is for new event creation
        if message == "NewEvent":
            event = request.data.pop('event')
            sport = event.pop('sport')
            markets = event.pop('markets')[0] # for now we have only one market
            selections = markets.pop('selections')
            sport = Sport.objects.create(**sport)
            markets = Market.objects.create(**markets, sport=sport)
            for selection in selections:
                markets.selections.create(**selection)
            match = Match.objects.create(**event, sport=sport, market=markets)
            return Response(status=status.HTTP_201_CREATED)
        # check if incoming api request is for updation of odds
        elif message == "UpdateOdds":
            event = request.data.pop('event')
            markets = event.pop('markets')[0]
            selections = markets.pop('selections')
            for selection in selections:
                s = Selection.objects.get(id=selection['id'])
                s.odds = selection['odds']
                s.save()
            match = Match.objects.get(id=event['id'])
            return Response(status=status.HTTP_201_CREATED)
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST)


"""
Les doc-strings que nous écrivons dans nos vues seront utilisées pour notre documentation, alors ne manquez pas cela Le 
get_serializer_class nous aide à trouver quel sérialiseur utiliser `list` ou` detail` en fonction de la vue 
Nous écrasons la méthode get_query_set pour filtrer par certains mots-clés comme `sport`,` name`, `ordering` 
Nous écrasons la méthode de création par défaut pour analyser la requête post json entrante d'une autre API. 
nous devons analyser le type de message et découvrir quel est le motif
"""