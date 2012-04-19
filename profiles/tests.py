from django.contrib.auth.models import User
from django.test import TestCase
from django_reputation.models import UserReputationAction
from test_utils import setupTreemapEnv, teardownTreemapEnv, mkPlot, mkTree

from utils import change_reputation_for_user

class TestUtils(TestCase):

    def setUp(self):
        teardownTreemapEnv() # In case a previous tearDown did not run
        setupTreemapEnv()
        self.jim = User.objects.get(username="jim")
        self.amy = User.objects.get(username="amy")

    def tearDown(self):
        teardownTreemapEnv()

    def test_change_reputation_for_action(self):
        plot = mkPlot(self.jim)
        tree = mkTree(self.jim, plot=plot)

        reputation_count = UserReputationAction.objects.count()
        self.assertEqual(0, reputation_count)

        change_reputation_for_user(self.jim, 'add tree', tree)

        self.assertEqual(1, UserReputationAction.objects.count())
        reputation_action = UserReputationAction.objects.all()[0]

        self.assertEqual(self.jim.id, reputation_action.user.id)
        self.assertEqual(self.jim.id, reputation_action.originating_user.id)
        self.assertEqual(25, reputation_action.value)

    def test_change_reputation_for_action_with_sub_actions(self):
        plot = mkPlot(self.jim)
        tree = mkTree(self.jim, plot=plot)

        reputation_count = UserReputationAction.objects.count()
        self.assertEqual(0, reputation_count)

        change_reputation_for_user(self.amy, 'edit verified', tree, sub_action='down', change_initiated_by_user=self.jim)

        self.assertEqual(1, UserReputationAction.objects.count())
        reputation_action = UserReputationAction.objects.all()[0]

        self.assertEqual(self.amy.id, reputation_action.user.id)
        self.assertEqual(self.jim.id, reputation_action.originating_user.id)
        self.assertEqual(-10, reputation_action.value)

    def test_change_reputation_for_user_raises_when_user_is_none(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, None, 'add plot', plot)

    def test_change_reputation_for_user_raises_when_action_is_none(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, self.jim, None, plot)

    def test_change_reputation_for_user_raises_when_target_model_is_none(self):
        self.assertRaises(Exception, change_reputation_for_user, self.jim, 'add plot', None)

    def test_change_reputation_for_user_raises_when_action_is_invalid(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, self.jim, '!!DANCE!!', plot)

    def test_change_reputation_for_user_raises_action_is_specified_without_sub_action(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, self.jim, 'edit verified', plot)

    def test_change_reputation_for_user_raises_when_sub_action_is_invalid(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, self.jim, 'edit verified', plot, sub_action='!!DANCE!!')

    def test_change_reputation_for_user_raises_when_sub_action_is_specified_for_action_that_does_not_support_it(self):
        plot = mkPlot(self.jim)
        self.assertRaises(Exception, change_reputation_for_user, self.jim, 'add tree', plot, sub_action='up')

